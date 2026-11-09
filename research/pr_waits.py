import subprocess, json, datetime, statistics
tz=datetime.timezone(datetime.timedelta(hours=-5))
r=subprocess.run(['gh','pr','list','--state','merged','--limit','200','--json','number,createdAt,mergedAt,author'],capture_output=True,text=True,check=True)
rows=[]
for p in json.loads(r.stdout):
    c=datetime.datetime.fromisoformat(p['createdAt'].replace('Z','+00:00')); m=datetime.datetime.fromisoformat(p['mergedAt'].replace('Z','+00:00'))
    rows.append((p['number'],c.astimezone(tz),m.astimezone(tz),(m-c).total_seconds()/3600))
rows.sort()
w=[x[3] for x in rows]
print(f"merged PRs {len(rows)}; open-to-merge hours: median {statistics.median(w):.2f}, mean {statistics.mean(w):.2f}, max {max(w):.1f}")
night=[x for x in rows if x[1].hour>=22 or x[1].hour<7]; day=[x for x in rows if x not in night]
for name,grp in (('opened 22:00-07:00',night),('opened 07:00-22:00',day)):
    if grp: print(f"{name}: n={len(grp)} median wait {statistics.median([x[3] for x in grp]):.2f} h, max {max(x[3] for x in grp):.1f} h")
print("longest five:")
for x in sorted(rows,key=lambda x:-x[3])[:5]: print(f"  #{x[0]} opened {x[1]:%d %H:%M} merged {x[2]:%d %H:%M} wait {x[3]:.1f} h")
gaps=[]; ms=sorted(x[2] for x in rows)
for a,b in zip(ms,ms[1:]): gaps.append(((b-a).total_seconds()/3600,a,b))
g=max(gaps); print(f"longest gap between merges: {g[0]:.1f} h, {g[1]:%d %H:%M} to {g[2]:%d %H:%M}")
