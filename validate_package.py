"""Independent checks of the released data, evidence bundle and source crosswalk."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
P=Path(__file__).resolve().parent/'data'
d=pd.read_csv(P/'incidents.csv');t=pd.read_csv(P/'telemetry.csv')
assert d.incident.is_unique and d.cluster.nunique()==600 and len(d)==2400
assert (d.groupby('cluster').size()==4).all()
assert (d.groupby('missing').size()==600).all()
assert len(t)==16800 and (t.groupby('incident').size()==7).all()
assert np.allclose(d.filter(regex='^p_').sum(axis=1),1)
assert ((d.posterior_pred==d.root).astype(int)==d.posterior_correct).all()
assert ((d.anomaly_pred==d.root).astype(int)==d.anomaly_correct).all()
assert (d.evidence_accept<=d.confidence_accept).all()
assert (d.loc[d.evidence_accept==1,'observed']>=3).all()
for cid,g in t.groupby('incident'):
    row=d.loc[d.incident==cid].iloc[0]
    assert g.observed.sum()==row.observed
    if row.evidence_accept:
        assert g.loc[g.node==row.posterior_pred,'observed'].iloc[0]==1
wide=t.pivot(index='node',columns='incident',values='observed')
# Each incident's observation sets are nested as missingness increases.
for _,g in d.groupby('cluster'):
    masks=wide[g.sort_values('missing').incident].to_numpy()
    assert (np.diff(masks,axis=1)<=0).all()
a=json.loads((P/'example_bundle.json').read_text())
m=a['manifest'];pub=Ed25519PublicKey.from_public_bytes(bytes.fromhex(a['public_key_hex']))
encoded=json.dumps(m,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
message=b'RCA-EVIDENCE-V1\x00'+encoded;sig=bytes.fromhex(a['signature_hex'])
pub.verify(sig,message)
for k,v in a['blobs'].items():
    assert hashlib.sha256(v.encode('ascii')).hexdigest()==m['evidence'][k]
try:
    pub.verify(sig,message+b'!')
except InvalidSignature:pass
else:raise AssertionError('Altered signed bytes passed verification')
r=pd.read_csv(P/'supplied_reference_audit.csv')
assert set(r.supplied_number)==set(range(1,90))
inv=json.loads((P/'reference_inventory.json').read_text())
ids={v['number'] for v in inv['active_references']}|set(r.reference_number)
assert ids==set(range(1,111))
print('PASS: observation dependence, masks, probabilities, acceptance invariants, signature, evidence hashes, and all 89 supplied references.')
