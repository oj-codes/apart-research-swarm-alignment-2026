"""Regression tests for failure, pagination, acknowledgement races, and coalescing."""
import importlib.util
import fcntl
import json
from pathlib import Path
import subprocess
import sys
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
                       'thread': 'test', 'participant': 'codex', 'gh': 'gh', 'repository': 'o/r'}
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
        deliver = lambda *_: calls.append(True) or dict(queue_status='accepted', resume_status='requested')
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
            self.assertEqual(w.poll(self.config, state, self.directory,
                deliver=lambda *_: dict(queue_status='accepted', resume_status='requested')), 'error')
        self.assertEqual(state['observed'], self.a)
        self.assertIn('health', state['pending'])
        self.assertEqual(state['health']['status'], 'error')

    def test_delivery_failure_retains_detected_work(self):
        state = {'observed': {}}
        def fail(*_):
            raise RuntimeError('offline')
        self.assertEqual(w.poll(self.config, state, self.directory, snapshot=self.a, deliver=fail), 'failed')
        self.assertEqual(state['pending'], self.a)
        self.assertEqual(state['health']['status'], 'ok')
        self.assertEqual(state['delivery']['phase'], 'failed')
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
            result = w.queue(self.config, self.directory, 'notice')
            self.assertEqual(result, dict(queue_status='accepted', resume_status='deferred_active_writer'))

    def test_other_resume_failure_is_not_reported_as_delivered(self):
        response = subprocess.CompletedProcess([], 0, 'Queued message abc', 'Warning: could not resume: missing thread')
        with patch.object(w, 'command', return_value=response):
            self.assertEqual(w.queue(self.config, self.directory, 'notice')['resume_status'], 'failed')

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

    def test_failed_first_poll_can_be_baselined_without_dropping_health_notice(self):
        state = {}
        deliver = lambda *_: dict(queue_status='accepted', resume_status='failed')
        with patch.object(w, 'collect', side_effect=RuntimeError('offline')):
            w.poll(self.config, state, self.directory, deliver=deliver)
        self.assertNotIn('observed', state)
        self.assertEqual(set(state['pending']), {'health'})
        self.assertEqual(w.poll(self.config, state, self.directory, baseline=True,
                               snapshot=self.a, deliver=deliver), 'failed')
        self.assertEqual(state['observed'], self.a)
        self.assertIn('recovered', state['pending']['health']['label'])

    def test_failed_baseline_then_success_does_not_require_reset(self):
        state = {}
        with patch.object(w, 'collect', side_effect=RuntimeError('offline')):
            with self.assertRaisesRegex(RuntimeError, 'offline'):
                w.poll(self.config, state, self.directory, baseline=True)
        self.assertEqual(w.poll(self.config, state, self.directory, baseline=True, snapshot=self.a), 'ok')

    def test_accepted_failed_resume_retries_after_interval(self):
        state = {'observed': {}}
        delivered = Mock(return_value=dict(queue_status='accepted', resume_status='failed'))
        with patch.object(w, 'now', return_value='2030-01-01T00:00:00+00:00'):
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
            w.poll(self.config, state, self.directory, snapshot=self.b, deliver=delivered)
        self.assertEqual(delivered.call_count, 1)
        with patch.object(w, 'now', return_value='2030-01-01T00:30:00+00:00'):
            w.poll(self.config, state, self.directory, snapshot=self.b, deliver=delivered)
        self.assertEqual(delivered.call_count, 2)
        self.assertEqual(state['delivery']['attempts'], 2)
        self.assertEqual(state['pending'], self.b)

    def test_queue_failure_can_recover_without_new_remote_change(self):
        state = {'observed': {}}
        delivered = Mock(side_effect=[RuntimeError('offline'),
            dict(queue_status='accepted', resume_status='requested')])
        with patch.object(w, 'now', return_value='2030-01-01T00:00:00+00:00'):
            self.assertEqual(w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered), 'failed')
        with patch.object(w, 'now', return_value='2030-01-01T00:30:00+00:00'):
            self.assertEqual(w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered), 'awaiting_receipt')
        self.assertEqual(state['delivery']['queue_status'], 'accepted')

    def test_matching_receipt_is_required_and_prevents_immediate_retry(self):
        state = {'observed': {}}
        delivered = Mock(return_value=dict(queue_status='accepted', resume_status='requested'))
        with patch.object(w, 'now', return_value='2030-01-01T00:00:00+00:00'):
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
            with self.assertRaisesRegex(RuntimeError, 'does not match'):
                w.receipt(state, 'wrong-notice')
            self.assertNotIn('last_receipt', state)
            w.receipt(state, state['delivery']['notice_id'])
            self.assertEqual(state['delivery']['phase'], 'awaiting_ack')
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
        self.assertEqual(delivered.call_count, 1)

    def test_retries_are_bounded_and_stall_is_visible(self):
        state = {'observed': {}}
        delivered = Mock(return_value=dict(queue_status='accepted', resume_status='deferred_active_writer'))
        for minute in (0, 30, 60, 90):
            hour, minute = divmod(minute, 60)
            with patch.object(w, 'now', return_value=f'2030-01-01T{hour:02}:{minute:02}:00+00:00'):
                w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
        self.assertEqual(delivered.call_count, 3)
        self.assertEqual(w.outcome(state), 'stalled')
        self.assertTrue(state['pending'])

    def test_confirmed_receipt_stops_retries_despite_slow_acknowledgement(self):
        state = {'observed': {}}
        delivered = Mock(return_value=dict(queue_status='accepted', resume_status='requested'))
        with patch.object(w, 'now', return_value='2030-01-01T00:00:00+00:00'):
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
            w.receipt(state, state['delivery']['notice_id'])
        for stamp in ('2030-01-01T00:30:00+00:00', '2030-01-01T05:00:00+00:00'):
            with patch.object(w, 'now', return_value=stamp):
                self.assertEqual(w.poll(self.config, state, self.directory,
                    snapshot=self.b, deliver=delivered), 'processing_delayed')
        self.assertEqual(delivered.call_count, 1)
        self.assertEqual(state['delivery']['attempts'], 1)
        self.assertEqual(state['pending'], self.b)
        self.assertEqual(state['health']['status'], 'ok')
        self.assertNotIn('error', state['delivery'])

    def test_receipt_after_last_attempt_is_not_delivery_stalled(self):
        state = {'observed': {}}
        delivered = Mock(return_value=dict(queue_status='accepted', resume_status='requested'))
        with patch.object(w, 'now', return_value='2030-01-01T00:00:00+00:00'):
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
            state['delivery']['attempts'] = 3
            w.receipt(state, state['delivery']['notice_id'])
        with patch.object(w, 'now', return_value='2030-01-01T01:00:00+00:00'):
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
        self.assertEqual(delivered.call_count, 1)
        self.assertEqual(state['delivery']['phase'], 'processing_delayed')
        self.assertNotIn('error', state['delivery'])

    def test_duplicate_receipt_does_not_restart_processing_clock(self):
        state = {'observed': {}}
        delivered = Mock(return_value=dict(queue_status='accepted', resume_status='requested'))
        first = '2030-01-01T00:00:00+00:00'
        with patch.object(w, 'now', return_value=first):
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
            w.receipt(state, state['delivery']['notice_id'])
        with patch.object(w, 'now', return_value='2030-01-01T01:00:00+00:00'):
            w.receipt(state, state['delivery']['notice_id'])
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
        self.assertEqual(state['delivery']['receipt_at'], first)
        self.assertEqual(state['delivery']['phase'], 'processing_delayed')
        self.assertEqual(delivered.call_count, 1)

    def test_receipt_requires_active_pending_notice(self):
        for state in ({}, {'last_delivery': {'notice_id': 'old'}},
                      {'delivery': {'notice_id': 'orphan'}, 'pending': {}}):
            with self.subTest(state=state):
                with self.assertRaisesRegex(RuntimeError, 'No active delivery'):
                    w.receipt(state, 'old')
                self.assertNotIn('last_receipt', state)

    def test_cli_receipt_without_active_notice_fails(self):
        result = subprocess.run([sys.executable, str(Path(w.__file__)), 'receipt', '--dir',
            str(self.directory), '--notice-id', 'old'], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn('No active delivery', result.stderr)
        self.assertNotIn('last_receipt', json.loads((self.directory/'state.json').read_text()))

    def test_legacy_missing_or_invalid_queue_time_does_not_crash_or_infer_receipt(self):
        for value in (None, '', 'invalid', '2030-01-01T00:00:00'):
            with self.subTest(queued_at=value):
                state = {'observed': {}, 'notice_queued': 'queued',
                         'last_receipt': '2030-01-01T00:00:00+00:00'}
                if value is not None:
                    state['queued_at'] = value
                delivered = Mock()
                with patch.object(w, 'now', return_value='2030-01-01T00:00:00+00:00'):
                    self.assertEqual(w.poll(self.config, state, self.directory,
                        snapshot=self.a, deliver=delivered), 'awaiting_receipt')
                delivered.assert_not_called()
                self.assertNotIn('receipt_at', state['delivery'])
                self.assertIn('migration_warning', state['delivery'])

    def test_legacy_delivery_migrates_without_duplicating_recent_notice(self):
        state = {'observed': {}, 'notice_queued': 'queued', 'queued_at': '2030-01-01T00:00:00+00:00',
                 'last_receipt': '2030-01-01T00:01:00+00:00'}
        delivered = Mock()
        with patch.object(w, 'now', return_value='2030-01-01T00:02:00+00:00'):
            w.poll(self.config, state, self.directory, snapshot=self.a, deliver=delivered)
        delivered.assert_not_called()
        self.assertEqual(state['delivery']['phase'], 'awaiting_ack')
        self.assertNotIn('notice_queued', state)

    def test_cli_failed_first_poll_then_baseline_recovers(self):
        flag = self.directory/'offline'
        flag.touch()
        gh = self.directory/'fake-gh'
        gh.write_text(f'''#!{sys.executable}
import json,pathlib,sys
if pathlib.Path({str(flag)!r}).exists():
 print('offline',file=sys.stderr);sys.exit(1)
if sys.argv[2]=='graphql':
 data={{'data':{{'repository':{{'discussions':{{'nodes':[], 'pageInfo':{{'hasNextPage':False,'endCursor':None}}}}}}}}}}
elif 'commits/main' in sys.argv[-1]:
 data={{'sha':'commit','html_url':'https://example/commit','commit':{{'tree':{{'sha':'tree'}}}}}}
elif '/git/trees/' in sys.argv[-1]:
 data={{'truncated':False,'tree':[]}}
else:
 data=[[]]
print(json.dumps(data))
''')
        gh.chmod(0o700)
        codex = self.directory/'fake-codex'
        codex.write_text(f'#!{sys.executable}\nprint("Queued message test")\n')
        codex.chmod(0o700)
        config = dict(self.config, gh=str(gh), codex=str(codex), workspace=str(self.directory), local_inbox=False)
        (self.directory/'config.json').write_text(json.dumps(config))
        def invoke(action):
            return subprocess.run([sys.executable, str(Path(w.__file__)), action, '--dir',
                str(self.directory)], capture_output=True, text=True, timeout=10)
        self.assertEqual(invoke('poll').returncode, 2)
        state = json.loads((self.directory/'state.json').read_text())
        self.assertNotIn('observed', state)
        self.assertIn('health', state['pending'])
        flag.unlink()
        result = invoke('baseline')
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.directory/'state.json').read_text())
        self.assertIn('observed', state)
        self.assertIn('recovered', state['pending']['health']['label'])
        self.assertEqual(state['health']['github_requests'], 6)

    def test_explicit_retry_keeps_pending_and_rejects_stale_token(self):
        state = {'observed': {}, 'health': {'status': 'ok'}, 'pending': dict(self.a),
                 'delivery': {'notice_id': 'old', 'phase': 'stalled', 'attempts': 3}}
        (self.directory/'state.json').write_text(json.dumps(state))
        args = [sys.executable, str(Path(w.__file__)), 'retry', '--dir', str(self.directory), '--token']
        self.assertEqual(subprocess.run(args + ['wrong'], capture_output=True).returncode, 2)
        self.assertEqual(subprocess.run(args + [w.digest(self.a)], capture_output=True).returncode, 0)
        saved = json.loads((self.directory/'state.json').read_text())
        self.assertEqual(saved['pending'], self.a)
        self.assertNotIn('delivery', saved)
        self.assertEqual(saved['last_delivery']['phase'], 'stalled')


if __name__ == '__main__':
    unittest.main(verbosity=2)
