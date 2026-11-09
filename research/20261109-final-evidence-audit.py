#!/usr/bin/env python3
"""Reproduce the numerical checks for the 9 November final evidence review.

Run from a full-history checkout with Python 3 and Poppler's pdftotext/pdffonts:
    python3 research/20261109-final-evidence-audit.py

Reads the current submission and pinned public history. Writes logs/results to
.local/final-evidence-20261109/ and runs the original five fixtures in a temporary,
isolated checkout. The fixed expectations identify this reviewed snapshot, not a
universal acceptance test. No model calls or Phase 4 experiments are made.
"""
from pathlib import Path
import ast, collections, concurrent.futures, datetime, hashlib, json, os, re, subprocess, tempfile, unicodedata, xml.etree.ElementTree as E, zipfile
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.local/final-evidence-20261109'
OUT.mkdir(parents=True, exist_ok=True)
PIN = 'b2ca5a7458027cd03ee94c3b9eaedae963165208'
ENV = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1', LC_ALL='C', LANG='C')
def run(args, cwd=ROOT):
    r = subprocess.run(args, cwd=cwd, env=ENV, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(f'{args}: {r.stdout}\n{r.stderr}')
    return r.stdout

def git(*args): return run(['git', *args])
def norm(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s).translate(str.maketrans({'’':"'", '“':'"', '”':'"'})))

build = (ROOT/'submission/build_docx.py').read_text()
tree = ast.parse(build)
abstract = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ABSTRACT' for t in n.targets))
figure_tree = ast.parse((ROOT/'submission/figure1.py').read_text())
figure_rows = next(ast.literal_eval(n.value) for n in figure_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='rows' for t in n.targets))
cutoff_text = re.search(r'fromisoformat\("([^"]+)"\)', (ROOT/'submission/split_by_convention.py').read_text()).group(1)
cutoff = datetime.datetime.fromisoformat(cutoff_text)
fmt='%H%x1f%aN%x1f%an%x1f%ae%x1f%aI%x1f%(trailers:key=Agent-Session,valueonly)%x1f%(trailers:key=Co-Authored-By,valueonly)%x1e'
log = git('-c', f'mailmap.blob={PIN}:.mailmap', 'log', PIN, '--no-merges', '--use-mailmap', f'--format={fmt}')
records=[]
for raw in log.split('\x1e'):
    if not raw.strip(): continue
    fields=raw.strip('\n').split('\x1f'); assert len(fields)==7
    sha, name, raw_name, email, when, session, coauthors=fields
    if name.startswith('O. J.'): continue
    records.append(dict(sha=sha,name=name,raw_name=raw_name,email=email,when=when,session=bool(session.strip()),coauthors=coauthors))
agg=collections.defaultdict(lambda:{'before':[0,0], 'after':[0,0]})
for r in records:
    bucket='before' if datetime.datetime.fromisoformat(r['when'])<cutoff else 'after'
    agg[r['name']][bucket][0]+=r['session']; agg[r['name']][bucket][1]+=1
assert {n:{'before':list(b),'after':list(a)} for n,first,b,a in figure_rows} == dict(agg)
findings=[f for f in git('ls-tree','-r','--name-only',PIN,'findings/').splitlines() if f.endswith('.md') and not f.endswith('README.md')]
authors=collections.Counter()
for f in findings:
    text=git('show',f'{PIN}:{f}')
    authors[re.search(r'^author:\s*(.+)$', text, re.M).group(1).strip().strip('\"\'')]+=1
coauthors=collections.Counter(line.split('<')[0].strip() for r in records for line in r['coauthors'].splitlines() if line.strip())
queries={}
for label,flags in [('default',[]),('unmapped',['--no-use-mailmap']),('mapped',['--use-mailmap'])]:
    queries[label]=len(git('-c',f'mailmap.blob={PIN}:.mailmap','log',PIN,'--no-merges','--author=Auran','--format=%H',*flags).splitlines())
assert queries=={'default':34,'unmapped':24,'mapped':34}

scratch=tempfile.TemporaryDirectory(prefix='codex-final-evidence-')
clone=Path(scratch.name)/'repo'
run(['git','clone','--shared','--no-checkout',str(ROOT),str(clone)])
run(['git','checkout','--detach',PIN],cwd=clone)
assert run(['git','rev-parse','HEAD'],cwd=clone).strip()==PIN
retrieval=run(['python3','-I','submission/eval/harness.py','--expect-scenarios','5'],cwd=clone)
(OUT/'pinned-retrieval.txt').write_text(retrieval)
counts={k:int(re.search(rf'^  {k}\s+(\d+)\s',retrieval,re.M).group(1)) for k in ['correct','missed_link','false_merge','insufficient_evidence']}
assert counts=={'correct':16,'missed_link':11,'false_merge':1,'insufficient_evidence':3}
agreement=[int(v) for v in re.search(r'(\d+)/(\d+) matched the recorded expectation',retrieval).groups()]
assert agreement==[31,31]

w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
with zipfile.ZipFile(ROOT/'submission/report.docx') as z: xml=E.fromstring(z.read('word/document.xml'))
paragraphs=[''.join(t.text or '' for t in p.iter(w+'t')) for p in xml.iter(w+'p')]
word='\n'.join(paragraphs)
(OUT/'docx-text.txt').write_text(word)
pdf=run(['pdftotext','-layout',str(ROOT/'submission/report.pdf'),'-'])
(OUT/'rendered.txt').write_text(pdf)
pages=pdf.split('\f')
if not pages[-1].strip(): pages.pop()
references=next((i+1,j) for i,p in enumerate(pages) for j,l in enumerate(p.splitlines()) if l.strip()=='References')
assert references==(9,0)
assert len(pages)==17
assert norm(abstract) in norm(pages[0])
assert all(p.strip().splitlines()[-1].strip()==str(i) for i,p in enumerate(pages,1))
assert '2.21' not in word
assert 'opt-in for plain git log' not in word
assert 'enough to find each participant' not in word
assert 'git log --no-merges --no-use-mailmap --author=Auran finds 24' in word
assert 'This grep is a shortcut specific to this fixture' in word
assert 'not a constant assignment across the sprint' in word
fonts=run(['pdffonts',str(ROOT/'submission/report.pdf')]); (OUT/'fonts.txt').write_text(fonts)
assert 'OldStandardTT-Regular' in fonts and 'OldStandardTT-Bold' in fonts and 'OldStandardTT-Italic' in fonts

checks=[]
required_checks = {
    'test_report_authors.py', 'test_report_budget.py', 'test_report_docx_fresh.py',
    'test_report_page_cap.py', 'test_report_pdf_fresh.py',
    'test_report_provenance.py', 'test_report_ship_record.py',
}
check_paths = sorted((ROOT/'submission').glob('test_report_*.py'))
assert required_checks <= {p.name for p in check_paths}, 'A required submission check is missing'
def check(p):
    r=subprocess.run(['python3','-I',str(p)],cwd=ROOT,env=ENV,capture_output=True,text=True)
    (OUT/f'{p.stem}.txt').write_text(r.stdout+r.stderr)
    return {'script':str(p.relative_to(ROOT)),'exit_code':r.returncode,'output':(r.stdout+r.stderr).strip()}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    checks=list(pool.map(check,check_paths))
assert len(checks)==len(check_paths) and all(c['exit_code']==0 for c in checks),checks
artifacts={n:{'sha256':hashlib.sha256((ROOT/'submission'/n).read_bytes()).hexdigest(),'bytes':(ROOT/'submission'/n).stat().st_size} for n in ['report.docx','report.pdf','build_docx.py']}
result={'checked_at_local_clock':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_revision':git('rev-parse','HEAD').strip(),'analysis_pin':PIN,'git_version':git('--version').strip(),'artifacts':artifacts,'abstract_words':len(abstract.split()),'pdf':{'pages':len(pages),'references_page':references[0],'references_line_index':references[1],'page_numbers_verified':len(pages)},'history':{'agent_nonmerge_commits':len(records),'with_session_trailer':sum(r['session'] for r in records),'convention_cutoff_from_paper':cutoff_text,'timestamp_basis':'Git author dates are user-controlled recorded metadata, not independently observed wall-clock times.','per_participant':dict(agg),'before':[sum(v['before'][i] for v in agg.values()) for i in [0,1]],'after':[sum(v['after'][i] for v in agg.values()) for i in [0,1]],'figure1_rows_match':True,'coauthor_labels':dict(coauthors),'findings_count':len(findings),'findings_by_author':dict(authors),'auran_query_counts':queries,'auran_raw_identity_tuples':len({(r['raw_name'],r['email']) for r in records if r['name']=='Auran'})},'retrieval':{'scenario_count':5,'outcomes':counts,'total':sum(counts.values()),'expectation_agreement':agreement,'interpretation':'Constructed cases with documented development revisions; no deployment rate or preregistration inference.'},'checks':checks}
result['audit_script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
result['history']['untrailered_before']=result['history']['before'][1]-result['history']['before'][0]
result['history']['post_convention_commits_from_new_arrivals']=sum(v['after'][1] for v in agg.values() if v['before'][1]==0)
assert result['history']['untrailered_before']==32
assert result['history']['post_convention_commits_from_new_arrivals']==28
scratch.cleanup()
(OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['artifacts','abstract_words','pdf','history','retrieval']},indent=2))
print(f'{len(checks)} checks passed; results saved to',OUT/'results.json')
