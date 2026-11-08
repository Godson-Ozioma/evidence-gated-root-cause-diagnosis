"""Synthetic microservice diagnosis and detached-signature experiment.
No production traces, human participants, or measured incident-response times.
Run: python run_study.py (Python 3.11+, numpy, pandas, matplotlib, cryptography).
"""
from pathlib import Path
import json, hashlib, copy, platform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

OUT=Path(__file__).resolve().parent
(OUT/'data').mkdir(exist_ok=True); (OUT/'figures').mkdir(exist_ok=True)
NAMES=['API','Auth','Account','Ledger','Payment','Audit','Database']
EDGES=[(0,1),(0,2),(2,3),(3,4),(3,5),(3,6)] # caller -> dependency
N=7; SEED=20261103; THRESHOLD=.90
FAMILIES=['Cascading latency','Pool saturation','Payload errors']
MISSING=[0.0,.15,.30,.45]
D=np.full((N,N),np.inf); np.fill_diagonal(D,0)
for a,b in EDGES:D[a,b]=1
for k in range(N):D=np.minimum(D,D[:,k,None]+D[None,k,:])

def means(root,family):
    d=D[:,root]; affected=np.isfinite(d); rootmask=np.arange(N)==root
    amplitude=np.where(affected,np.where(rootmask,3.,2.+.4*np.where(affected,d,0)),0.)
    amplitude*= [1.,1.15,.85][family]
    onset=np.where(affected,.6*np.where(affected,d,0),4.)
    return np.r_[amplitude,onset]

COV=np.zeros((2*N,2*N))
COV[:N,:N]=1.1**2*np.eye(N)+.35**2*np.ones((N,N))
COV[N:,N:]=.8**2*np.eye(N)+.3**2*np.ones((N,N))
MEANS=np.array([[means(r,f) for r in range(N)] for f in range(3)])
cache={}
def posterior(y,mask,family):
    key=tuple(bool(x) for x in mask)
    if key not in cache:
        ids=np.r_[np.flatnonzero(mask),N+np.flatnonzero(mask)]
        cache[key]=(ids,np.linalg.inv(COV[np.ix_(ids,ids)]))
    ids,inv=cache[key]
    delta=y[ids]-MEANS[family][:,ids]
    scores=-.5*np.einsum('ki,ij,kj->k',delta,inv,delta)
    scores-=scores.max(); prob=np.exp(scores); return prob/prob.sum()

def canonical(value):
    # Restricted ASCII JSON: integral metadata and decimal-string measurements.
    # This is a documented local serialization profile, not a general JCS implementation.
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def digest(blob):return hashlib.sha256(blob).hexdigest()
# Public reproducibility fixture ONLY. Never use this deterministic test key in deployment.
key=Ed25519PrivateKey.from_private_bytes(hashlib.sha256(b'PUBLIC-SIMULATION-TEST-KEY-20261103').digest())
pub=key.public_key()

def artifact(cid,y,mask,pred,prob):
    blobs={}
    for k in np.flatnonzero(mask):
        blobs[NAMES[k]]=canonical({'incident':cid,'node':NAMES[k],
            'amplitude':format(y[k],'.17g'),'onset':format(y[N+k],'.17g')})
    manifest={'schema':'synthetic-rca-evidence-v1','incident':cid,'environment':'synthetic',
        'model':'gaussian-graph-v1','rule':'reverse-dependency-likelihood-v1',
        'root':NAMES[pred],'posterior':format(prob[pred],'.17g'),
        'human_review':'not_performed','evidence':{k:digest(v) for k,v in blobs.items()}}
    sig=key.sign(b'RCA-EVIDENCE-V1\x00'+canonical(manifest))
    return manifest,blobs,sig

def verify(manifest,blobs,sig,expected_incident):
    try:
        if manifest['incident']!=expected_incident:return False
        pub.verify(sig,b'RCA-EVIDENCE-V1\x00'+canonical(manifest))
        if set(blobs)!=set(manifest['evidence']):return False
        for node,h in manifest['evidence'].items():
            if digest(blobs[node])!=h:return False
            b=json.loads(blobs[node])
            if b['incident']!=expected_incident or b['node']!=node:return False
        return True
    except Exception:return False

rows=[]; telemetry=[]; fixtures=[]
for f in range(3):
    for rep in range(200):
        rng=np.random.default_rng(np.random.SeedSequence([SEED,f,rep]))
        root=int(rng.integers(N)); y=rng.multivariate_normal(MEANS[f,root],COV)
        uniforms=rng.uniform(size=N); base=f*200+rep
        for missing in MISSING:
            mask=uniforms>=missing
            p=posterior(y,mask,f); pred=int(np.argmax(p))
            baseline=int(np.argmax(np.where(mask,y[:N],-np.inf)))
            if not mask.any():baseline=0
            cid=f'I{base:04d}-M{int(missing*100):02d}'
            m,b,s=artifact(cid,y,mask,pred,p)
            integrity=verify(m,b,s,cid)
            confidence=bool(p[pred]>=THRESHOLD)
            evidence=bool(confidence and mask[pred] and mask.sum()>=3 and integrity)
            probs={f'p_{n}':p[j] for j,n in enumerate(NAMES)}
            rows.append(dict(incident=cid,cluster=base,family=FAMILIES[f],missing=missing,
                root=NAMES[root],observed=int(mask.sum()),anomaly_pred=NAMES[baseline],
                posterior_pred=NAMES[pred],anomaly_correct=int(baseline==root),
                posterior_correct=int(pred==root),confidence=float(p[pred]),
                confidence_accept=int(confidence),evidence_accept=int(evidence),
                root_record_present=int(mask[pred]),integrity=int(integrity),**probs))
            for j in range(N):telemetry.append(dict(incident=cid,node=NAMES[j],
                amplitude=y[j],onset=y[N+j],observed=int(mask[j]),synthetic_root=int(j==root)))
            if missing==0 and len(fixtures)<200: fixtures.append((m,b,s,root))
df=pd.DataFrame(rows); df.to_csv(OUT/'data/incidents.csv',index=False)
pd.DataFrame(telemetry).to_csv(OUT/'data/telemetry.csv',index=False)

def summarize(g):
    result={'n':len(g),'anomaly_accuracy':g.anomaly_correct.mean(),
            'posterior_accuracy':g.posterior_correct.mean()}
    for mode in ['confidence','evidence']:
        accepted=g[f'{mode}_accept'].astype(bool)
        result[f'{mode}_coverage']=accepted.mean()
        result[f'{mode}_accuracy']=g.loc[accepted,'posterior_correct'].mean()
        result[f'{mode}_correct_yield']=(accepted*g.posterior_correct).mean()
        result[f'{mode}_accepted']=int(accepted.sum())
        result[f'{mode}_wrong']=int((accepted*(1-g.posterior_correct)).sum())
    return result
summary={str(k):summarize(g) for k,g in df.groupby('missing')}
summary['pooled']=summarize(df)
summary['family']={k:summarize(g) for k,g in df.groupby('family')}
# Cluster bootstrap: preserve all four missingness views from each independent incident.
rng=np.random.default_rng(SEED+1); mat=df.sort_values(['cluster','missing'])
metrics=[]
for _ in range(2000):
    selected=rng.integers(0,600,600)
    g=mat.iloc[(selected[:,None]*4+np.arange(4)[None,:]).ravel()]
    s=summarize(g)
    metrics.append([s['posterior_accuracy']-s['anomaly_accuracy'],s['evidence_coverage'],s['evidence_accuracy'],s['evidence_correct_yield']])
summary['bootstrap95']={name:np.quantile(np.array(metrics)[:,j],[.025,.975]).tolist()
    for j,name in enumerate(['posterior_minus_anomaly','evidence_coverage','evidence_accuracy','evidence_correct_yield'])}
summary['bootstrap_replicates']=2000

# Fixed sensitivity: confidence thresholds; no test-data threshold selection.
curves=[]
for threshold in [.5,.6,.7,.8,.85,.9,.95,.99]:
    for mode in ['confidence','evidence']:
        take=df.confidence>=threshold
        if mode=='evidence':take &= (df.root_record_present==1)&(df.observed>=3)&(df.integrity==1)
        curves.append(dict(threshold=threshold,mode=mode,coverage=take.mean(),
            risk=1-df.loc[take,'posterior_correct'].mean(),accepted=int(take.sum())))
pd.DataFrame(curves).to_csv(OUT/'data/risk_coverage.csv',index=False)

# Deliberate model mismatch: same base seeds; weakened root amplitude and extra onset noise.
stress=[]
for f in range(3):
    for rep in range(200):
        rng=np.random.default_rng(np.random.SeedSequence([SEED,f,rep]))
        root=int(rng.integers(N)); y=rng.multivariate_normal(MEANS[f,root],COV)
        uniforms=rng.uniform(size=N)
        y[root]*=.6; y[N:]+=rng.normal(0,1.2,N)
        mask=uniforms>=.30; p=posterior(y,mask,f); pred=int(np.argmax(p))
        take=bool(p[pred]>=THRESHOLD and mask[pred] and mask.sum()>=3)
        stress.append(dict(cluster=f*200+rep,root=NAMES[root],pred=NAMES[pred],
            correct=int(pred==root),accept=int(take)))
st=pd.DataFrame(stress); st.to_csv(OUT/'data/model_mismatch.csv',index=False)
summary['mismatch']={'n':len(st),'accuracy':st.correct.mean(),'coverage':st.accept.mean(),
    'accepted_accuracy':st.loc[st.accept==1,'correct'].mean(),'accepted':int(st.accept.sum())}

# Paired integrity mutations. Verification checks evidence binding, not causal truth.
checks=[]
for m,b,s,truth in fixtures:
    cid=m['incident']
    for kind in ['clean','alter_telemetry','alter_conclusion','alter_rule','remove_blob','cross_incident','resigned_false_claim']:
        mm=copy.deepcopy(m); bb=copy.deepcopy(b); ss=s; expected=cid
        if kind=='alter_telemetry':bb[next(iter(bb))]+=b' '
        if kind=='alter_conclusion':mm['root']='INVALID'
        if kind=='alter_rule':mm['rule']='unrecorded-rule'
        if kind=='remove_blob':bb.pop(next(iter(bb)))
        if kind=='cross_incident':expected=cid+'-other'
        if kind=='resigned_false_claim':
            mm['root']=NAMES[(truth+1)%N]
            ss=key.sign(b'RCA-EVIDENCE-V1\x00'+canonical(mm))
        checks.append(dict(incident=cid,mutation=kind,accepted=int(verify(mm,bb,ss,expected))))
ck=pd.DataFrame(checks); ck.to_csv(OUT/'data/integrity_checks.csv',index=False)
summary['integrity']={kind:{'n':len(g),'accepted':int(g.accepted.sum())} for kind,g in ck.groupby('mutation')}
m,b,s,_=fixtures[0]
(OUT/'data/example_manifest.json').write_text(json.dumps(m,indent=2))
(OUT/'data/example_bundle.json').write_text(json.dumps({'manifest':m,
    'blobs':{k:v.decode() for k,v in b.items()},'signature_hex':s.hex(),
    'public_key_hex':pub.public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()},indent=2))
summary['seed']=SEED; summary['independent_incidents']=600
summary['python']=platform.python_version(); summary['numpy']=np.__version__
(OUT/'data/summary.json').write_text(json.dumps(summary,indent=2))

# Publication figures use exact outputs, with no generated illustrative measurements.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
    'axes.spines.right':False,'savefig.dpi':300,'axes.titleweight':'bold'})
cols=['#9A4A24','#245B82','#31765C','#7A5A91']
fig,ax=plt.subplots(figsize=(7.0,3.5))
x=np.array(MISSING)*100
ax.plot(x,[summary[str(v)]['anomaly_accuracy']*100 for v in MISSING],'o-',color=cols[0],label='Largest observed anomaly')
ax.plot(x,[summary[str(v)]['posterior_accuracy']*100 for v in MISSING],'s-',color=cols[1],label='Graph likelihood | all cases')
ax.plot(x,[summary[str(v)]['evidence_accuracy']*100 for v in MISSING],'^-',color=cols[2],label='Evidence gate | accepted cases')
ax.set(xlabel='Probability of a missing service record (%)',ylabel='Correct root diagnosis (%)',ylim=(0,105))
ax.grid(alpha=.18); ax.legend(loc='lower left',fontsize=9); fig.tight_layout()
fig.savefig(OUT/'figures/figure1_accuracy.png'); plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(7.0,3.3))
for mode,color,label in [('confidence',cols[1],'Confidence only'),('evidence',cols[2],'Evidence gate')]:
    c=pd.DataFrame(curves); c=c[c['mode']==mode]
    axs[0].plot(c.coverage*100,c.risk*100,'o-',color=color,label=label)
    t=c[c.threshold==.9].iloc[0]; axs[0].annotate('0.90',xy=(t.coverage*100,t.risk*100),xytext=(4,6),textcoords='offset points',fontsize=8)
axs[0].set(xlabel='Coverage (%)',ylabel='Error among accepted cases (%)');axs[0].legend(fontsize=8);axs[0].grid(alpha=.18)
width=5
axs[1].bar(x-width/2,[summary[str(v)]['evidence_coverage']*100 for v in MISSING],width,color=cols[2],label='Accepted')
axs[1].bar(x+width/2,[summary[str(v)]['evidence_correct_yield']*100 for v in MISSING],width,color=cols[1],label='Accepted and correct')
axs[1].set(xlabel='Missingness (%)',ylabel='Share of all cases (%)',xticks=x,ylim=(0,105));axs[1].legend(fontsize=8)
fig.tight_layout();fig.savefig(OUT/'figures/figure2_coverage.png');plt.close(fig)
fig,ax=plt.subplots(figsize=(7.0,3.3))
kinds=['clean','alter_telemetry','alter_conclusion','alter_rule','remove_blob','cross_incident','resigned_false_claim']
labels=['Clean','Telemetry\nchanged','Conclusion\nchanged','Rule\nchanged','Evidence\nremoved','Wrong\nincident','False claim\nre-signed']
values=[summary['integrity'][k]['accepted']/2 for k in kinds]
bars=ax.bar(np.arange(7),values,color=[cols[2]]+[cols[1]]*5+[cols[0]])
ax.set(xticks=np.arange(7),xticklabels=labels,ylabel='Accepted by integrity verifier (%)',ylim=(0,115))
for bar,v in zip(bars,values):ax.text(bar.get_x()+bar.get_width()/2,v+2,f'{v:.0f}%',ha='center',fontsize=9)
ax.text(.99,.93,'200 checks per category',transform=ax.transAxes,ha='right',fontsize=9)
fig.tight_layout();fig.savefig(OUT/'figures/figure3_integrity.png');plt.close(fig)
print(json.dumps(summary,indent=2))
