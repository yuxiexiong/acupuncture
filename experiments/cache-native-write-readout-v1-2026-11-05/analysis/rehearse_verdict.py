"""NWR-01 判读离线预演：合同 §5 的四档标签在合成数据上既能判支持，也能判不可判/不支持/异号。
不读模型、不读真实数据。用法：python3 -I rehearse_verdict.py
"""
import random, statistics as st

SCENES = 6
def label(dM_native, dM_rand, dY_native, dY_rand, scene_signs_M, scene_signs_Y):
    """dM_native: 场景等权 ΔM；dM_rand: 随机臂 ΔM 列表；scene_signs_*: 各场景 Δ 的符号列表（-1/0/+1）。"""
    if dM_native >= 0.25 or dY_native >= 2:
        return "异号"
    dirM = dM_native <= -0.25 and sum(1 for s in scene_signs_M if s < 0) >= 4
    dirY = dY_native <= -2 and sum(1 for s in scene_signs_Y if s < 0) >= 2
    if not (dirM and dirY):
        return "不支持"
    if max(dM_rand) - min(dM_rand) > 1.0 or max(dY_rand) - min(dY_rand) > 6:
        return "不可判"
    sdM = st.stdev(dM_rand) if len(dM_rand) > 1 else 0.0
    sdY = st.stdev(dY_rand) if len(dY_rand) > 1 else 0.0
    lowM = st.mean(dM_rand) - 2 * sdM
    lowY = st.mean(dY_rand) - 2 * sdY
    specific = (dM_native <= lowM - 0.25) and (dY_native <= lowY - 2)
    return "支持" if specific else "不可判"

def case(name, dM, dY, rand_M, rand_Y, sM=None, sY=None):
    sM = sM or [-1] * SCENES
    sY = sY or [-1] * SCENES
    print(f"{name:28s} ΔM={dM:+.2f} ΔY={dY:+d} 随机M={['%+.2f'%x for x in rand_M]} 随机Y={rand_Y} → {label(dM, rand_M, dY, rand_Y, sM, sY)}")

random.seed(0)
small_M = [random.gauss(-0.05, 0.08) for _ in range(5)]
small_Y = [random.choice([-1, 0, 0, 1, -2]) for _ in range(5)]
big_M = [random.gauss(-1.8, 0.2) for _ in range(5)]
big_Y = [random.choice([-14, -16, -12, -15, -13]) for _ in range(5)]
wide_M = [-0.1, -1.4, -0.3, -0.9, -1.6]

print("合同 §5 四档预演（合成数据）")
case("A 原生强撤回、随机小", -2.0, -19, small_M, small_Y)
case("B 原生强撤回、随机同样强", -2.0, -19, big_M, big_Y)
case("C 原生弱、不达定向", -0.15, -1, small_M, small_Y, sM=[-1, -1, 1, 1, 0, -1])
case("D 原生反向", +0.6, +4, small_M, small_Y, sM=[1] * 6, sY=[1] * 6)
case("E 定向但场景不齐", -0.6, -5, small_M, small_Y, sM=[-1, -1, -1, 1, 1, 0])
case("F 随机带过宽", -2.0, -19, wide_M, [-3, -14, -6, -10, -18])
case("G 边缘：差距不足 0.25", -0.45, -5, small_M, small_Y)
