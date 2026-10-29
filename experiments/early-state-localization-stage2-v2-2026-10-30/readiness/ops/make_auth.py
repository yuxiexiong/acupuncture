"""Write one stage authorization for early-state-localization-stage2 with the project writer (exp.write).

python make_auth.py EXPERIMENT_DIR STAGE [key=relative_path ...]
"""
from pathlib import Path
import sys

here = Path(sys.argv[1]).resolve()
stage = sys.argv[2]
sys.path.insert(0, str(here))
import stage2 as S  # noqa: E402

exp = S.exp
USER = ('2026-10-30 用户原话：“授权全流程，每卡4个worker，表里全部预先放行，直接跑完，开跑后每30min汇报一次实验进程，eta”。'
        '“表里全部预先放行”指上一条回复中的表：实现说明待确认项按默认接受；II-B 新题由模型辅助审核并披露（失败可在任何 G 输出打开前修订一次，再失败停止）；'
        '阶段间选择锁定按冻结脚本机械执行；不改设计的工程修复每阶段最多重试 2 次；跑完后的阅读、分析、报告一并授权。'
        '资源上限（取上一条回复的示例值）：墙钟 30 小时、磁盘 40 GiB。合同级意外（§10 第四类状态、任何设计改动）须停止等待用户。')
auth = {'status': 'authorized', 'experiment': S.HERE.name, 'stage': stage, 'user_instruction': USER,
        'allowed_stages': [stage], 'maximum_workers': 8, 'workers_per_gpu': 4,
        'freeze_path': 'freeze-r01.json', 'freeze_sha256': exp.sha(here / 'freeze-r01.json'),
        'output_root': f'runs/{stage}-r01', 'resource_limits': {'wall_hours_total': 30, 'disk_gib_total': 40},
        'required_evidence': {}, 'created_at': exp.utc()}
for arg in sys.argv[3:]:
    key, rel = arg.split('=', 1)
    if key == 'output_root':
        auth['output_root'] = rel
        continue
    auth[key] = rel
    if key != 'g_development_run':
        auth['required_evidence'][rel] = exp.sha(here / rel)
if 'g_lock_path' in auth:
    auth['selection'] = exp.read(here / auth['g_lock_path'])['selection']
if 'a_lock_path' in auth:
    auth['candidates'] = exp.read(here / auth['a_lock_path'])['candidates']
path = here / f'readiness/authorization-{Path(auth["output_root"]).name}.json'
exp.write(path, auth, immutable=True)
S.authorize(path, stage)
print(path.relative_to(here), exp.sha(path))
