"""Regression tests for failure, pagination, acknowledgement races, and coalescing."""
import importlib.util
import fcntl
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('weekend_watch', Path(__file__).with_name('watch.py'))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.config = {'stop_at': '2099-01-01T00:00:00+00:00', 'codex': 'codex',
                       'thread': 'test', 'participant': 'codex'}
        self.a = {'comment:1': {'hash': 'a', 'label': 'First'}}
        self.b = {'comment:1': {'hash': 'b', 'label': 'Edited'}}

    def test_baseline_never_queues(self):
        state = {}
        self.assertEqual(w.poll(self.config, state, self.directory, True, self.a), 'ok')
        self.assertEqual(state['observed'], self.a)
        self.assertFalse(state.get('pending'))

    def test_changes_accumulate_under_one_notice(self):
        state = {'observed': {}}
        calls = []
        deliver = lambda *_: calls.append(True) or 'queued'
        w.poll(self.config, state, self.directory, snapshot=self.a, deliver=deliver)
        w.poll(self.config, state, self.directory, snapshot=self.b, deliver=deliver)
        self.assertEqual(len(calls), 1)
        self.assertEqual(state['pending'], self.b)

    def test_unseen_event_cannot_be_acknowledged(self):
        state = {'pending': dict(self.a), 'notice_queued': 'queued'}
        token = w.digest(state['pending'])
        state['pending'].update(self.b)
        with self.assertRaisesRegex(RuntimeError, 'changed'):
            w.acknowledge(state, token)
        self.assertEqual(state['pending'], self.b)

    def test_ack_allows_next_notice(self):
        state = {'pending': dict(self.a), 'notice_queued': 'queued'}
        w.acknowledge(state, w.digest(state['pending']))
        self.assertEqual(state['pending'], {})
        self.assertNotIn('notice_queued', state)

    def test_baseline_refuses_unread_batch(self):
        state = {'observed': {}, 'pending': dict(self.a)}
        with self.assertRaisesRegex(RuntimeError, 'unread'):
            w.poll(self.config, state, self.directory, True, self.b)
        self.assertEqual(state['pending'], self.a)

    def test_failed_feed_preserves_snapshot_and_notifies_health(self):
        state = {'observed': dict(self.a)}
        with patch.object(w, 'collect', side_effect=RuntimeError('feed failed')):
            self.assertEqual(w.poll(self.config, state, self.directory, deliver=lambda *_: 'queued'), 'error')
        self.assertEqual(state['observed'], self.a)
        self.assertIn('health', state['pending'])
        self.assertEqual(state['health']['status'], 'error')

    def test_delivery_failure_retains_detected_work(self):
        state = {'observed': {}}
        def fail(*_):
            raise RuntimeError('offline')
        with self.assertRaisesRegex(RuntimeError, 'offline'):
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=fail)
        self.assertEqual(state['pending'], self.a)
        self.assertEqual(state['health']['status'], 'delivery_error')
        self.assertEqual(json.loads((self.directory/'state.json').read_text())['pending'], self.a)

    def test_expiry_makes_no_network_or_model_calls(self):
        self.config['stop_at'] = '2000-01-01T00:00:00+00:00'
        with patch.object(w, 'collect', side_effect=AssertionError('network')):
            self.assertEqual(w.poll(self.config, {}, self.directory), 'expired')

    def test_edit_and_deletion_both_detected(self):
        self.assertEqual(w.changes(self.a, self.b), self.b)
        self.assertEqual(w.changes(self.a, {})['comment:1']['hash'], 'removed')

    def test_resume_active_writer_is_unverified(self):
        response = subprocess.CompletedProcess([], 0, 'Queued message abc', 'Warning: could not resume: already has an active writer')
        with patch.object(w, 'command', return_value=response):
            self.assertIn('unverified', w.queue(self.config, self.directory))

    def test_other_resume_failure_is_not_reported_as_delivered(self):
        response = subprocess.CompletedProcess([], 0, 'Queued message abc', 'Warning: could not resume: missing thread')
        with patch.object(w, 'command', return_value=response):
            self.assertIn('manual attention', w.queue(self.config, self.directory))

    def test_rest_uses_all_pages(self):
        response = subprocess.CompletedProcess([], 0, '[[{"id":1}],[{"id":2}]]', '')
        with patch.object(w, 'command', return_value=response) as call:
            self.assertEqual(w.GitHub('gh', 'o/r').rest('pulls'), [{'id': 1}, {'id': 2}])
        self.assertIn('--paginate', call.call_args.args[0])

    def test_reply_connection_follows_cursor(self):
        pages = [dict(node=dict(replies=dict(nodes=[{'id': 'a'}], pageInfo=dict(hasNextPage=True, endCursor='next')))),
                 dict(node=dict(replies=dict(nodes=[{'id': 'b'}], pageInfo=dict(hasNextPage=False, endCursor='end'))))]
        gh = w.GitHub('gh', 'o/r')
        with patch.object(gh, 'graphql', side_effect=pages) as call:
            self.assertEqual(list(gh.connection('replies', 'parent')), [{'id': 'a'}, {'id': 'b'}])
        self.assertEqual(call.call_args.kwargs['cursor'], 'next')

    def test_graphql_errors_are_not_empty_feed(self):
        response = subprocess.CompletedProcess([], 0, '{"data":{},"errors":[{"message":"denied"}]}', '')
        with patch.object(w, 'command', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'errors'):
                w.GitHub('gh', 'o/r').graphql('query {}')

    def test_second_process_cannot_touch_locked_state(self):
        with (self.directory/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = subprocess.run(['python3', str(Path(w.__file__)), 'status', '--dir',
                                     str(self.directory)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertIn('another invocation', result.stdout)
        self.assertFalse((self.directory/'state.json').exists())

    def test_corrupt_state_is_not_silently_rebaselined(self):
        path = self.directory/'state.json'
        path.write_text('{broken')
        result = subprocess.run(['python3', str(Path(w.__file__)), 'baseline', '--dir',
                                 str(self.directory)], capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_text(), '{broken')

    def test_remote_letters_and_replies_work_without_local_disk_access(self):
        gh = Mock()
        gh.rest.return_value = []
        def connection(kind, parent=None):
            rows = {'discussions': [{'id': 'd', 'number': 9, 'url': 'https://example/d'}],
                    'comments': [{'id': 'c', 'url': 'https://example/c'}],
                    'replies': [{'id': 'r', 'url': 'https://example/r'}]}
            return iter(rows[kind])
        gh.connection.side_effect = connection
        gh.api.side_effect = [dict(sha='commit', html_url='https://example/commit',
                                   commit=dict(tree=dict(sha='tree'))),
                              dict(truncated=False, tree=[dict(type='blob', path='inbox/codex/letter.md', sha='letter')])]
        config = dict(self.config, repository='o/r', workspace='/protected', local_inbox=False)
        with patch.object(Path, 'exists', side_effect=PermissionError('protected')):
            events = w.collect(config, gh)
        self.assertIn('letter:main:inbox/codex/letter.md', events)
        self.assertIn('reply:r', events)

    def test_truncated_remote_inbox_is_a_failed_snapshot(self):
        gh = Mock()
        gh.rest.return_value = []
        gh.connection.return_value = []
        gh.api.side_effect = [dict(sha='commit', html_url='https://example/commit',
                                   commit=dict(tree=dict(sha='tree'))), dict(truncated=True, tree=[])]
        with self.assertRaisesRegex(RuntimeError, 'truncated'):
            w.collect(dict(self.config, repository='o/r'), gh)


if __name__ == '__main__':
    unittest.main(verbosity=2)
