
import math

from openfhe import *

# python 01_basics/07_rotation.py
#
# 슬롯 회전(EvalRotate)과 이를 이용한 합계 / 내적 계산
#
# 지금까지의 덧셈/곱셈은 모두 "같은 슬롯끼리" 계산하는 SIMD 연산이었다.
#   [a0, a1, a2, a3] * [b0, b1, b2, b3] = [a0*b0, a1*b1, a2*b2, a3*b3]
#
# 하지만 내적, 합계, 행렬-벡터 곱처럼 "다른 슬롯의 값을 섞어야 하는" 연산은
# 슬롯을 이동시키는 회전(rotation)이 있어야 가능하다.


def decrypt_vector(cc, secret_key, ciphertext, length, digits=6):
    plaintext = cc.Decrypt(secret_key, ciphertext)
    plaintext.SetLength(length)
    values = plaintext.GetRealPackedValue()
    if digits is None:
        return values
    return [round(v, digits) for v in values]


def main():
    batch_size = 8

    # 1. CKKS 파라미터 생성
    parameters = CCParamsCKKSRNS()
    parameters.SetMultiplicativeDepth(2)
    parameters.SetScalingModSize(50)
    parameters.SetBatchSize(batch_size)

    # 2. CryptoContext 생성
    cc = GenCryptoContext(parameters)

    # 3. 암호 시스템 기능 활성화
    cc.Enable(PKESchemeFeature.PKE)
    cc.Enable(PKESchemeFeature.KEYSWITCH)
    cc.Enable(PKESchemeFeature.LEVELEDSHE)
    cc.Enable(PKESchemeFeature.ADVANCEDSHE)  # EvalSum, EvalInnerProduct 사용

    # 4. 키 생성
    keys = cc.KeyGen()
    cc.EvalMultKeyGen(keys.secretKey)

    # 5. 회전 키 생성
    #    회전도 key switching이 필요하므로, 사용할 회전 거리마다 키를 미리 만들어야 한다.
    #    양수 = 왼쪽 회전, 음수 = 오른쪽 회전
    #    1, 2, 4 는 합계(EvalSum)를 직접 구현할 때 사용
    rotation_indices = [1, 2, 4, -1]
    cc.EvalRotateKeyGen(keys.secretKey, rotation_indices)

    # 6. 원본 벡터 (batch_size만큼 채움)
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    plaintext = cc.MakeCKKSPackedPlaintext(values)
    ciphertext = cc.Encrypt(keys.publicKey, plaintext)

    # ------------------------------------------------------------
    # 실험 1. 기본 회전
    # ------------------------------------------------------------
    print("=" * 60)
    print("실험 1. EvalRotate: 슬롯 회전")
    print("=" * 60)
    print("Original        :", values)

    for k in [1, 2, -1]:
        rotated = cc.EvalRotate(ciphertext, k)
        expected = values[k:] + values[:k]  # 왼쪽으로 k칸 순환 이동
        print(f"Rotate({k:>2})      :", decrypt_vector(cc, keys.secretKey, rotated, batch_size))
        print(f"  expected      : {expected}")

    rotated = cc.EvalRotate(ciphertext, 1)
    print(f"\nlevel: 회전 전 = {ciphertext.GetLevel()}, 회전 후 = {rotated.GetLevel()}"
          "  -> 회전은 level을 소모하지 않는다")

    # 회전 키를 만들지 않은 거리로 회전하면 실패한다
    try:
        cc.EvalRotate(ciphertext, 3)
        print("Rotate(3)       : 성공")
    except Exception as e:
        reason = "EvalKey" + str(e).split("EvalKey", 1)[1].split("[called", 1)[0] if "EvalKey" in str(e) else str(e)
        print(f"Rotate(3)       : 실패 (회전 키 없음) -> {reason.strip()}")

    # ------------------------------------------------------------
    # 실험 2. 회전 + 덧셈으로 전체 합 계산 (rotate-and-sum)
    # ------------------------------------------------------------
    print()
    print("=" * 60)
    print("실험 2. 회전 + 덧셈으로 전체 합 계산")
    print("=" * 60)

    #   step 1: x + Rot(x, 1) -> 이웃한 2개의 합
    #   step 2: 위 결과 + Rot(위 결과, 2) -> 4개의 합
    #   step 3: 위 결과 + Rot(위 결과, 4) -> 8개의 합
    # 슬롯 n개의 합을 n-1번이 아니라 log2(n)번의 회전으로 구할 수 있다.
    acc = ciphertext
    step = 1
    while step < batch_size:
        acc = cc.EvalAdd(acc, cc.EvalRotate(acc, step))
        print(f"Rotate {step} + Add  :", decrypt_vector(cc, keys.secretKey, acc, batch_size))
        step *= 2

    print(f"expected sum    : {sum(values)} (모든 슬롯에 같은 합이 들어감)")
    print(f"회전 횟수       : {int(math.log2(batch_size))}번 (단순 방식이면 {batch_size - 1}번)")

    # OpenFHE 내장 함수 EvalSum으로도 같은 결과를 얻을 수 있다
    cc.EvalSumKeyGen(keys.secretKey)
    summed = cc.EvalSum(ciphertext, batch_size)
    print("EvalSum         :", decrypt_vector(cc, keys.secretKey, summed, batch_size))

    # ------------------------------------------------------------
    # 실험 3. 암호문 내적 (곱셈 + 합)
    # ------------------------------------------------------------
    print()
    print("=" * 60)
    print("실험 3. 암호문 내적 = EvalMult + rotate-and-sum")
    print("=" * 60)

    weights = [0.5, -1.0, 2.0, 0.0, 1.5, -0.5, 1.0, 0.25]
    ct_weights = cc.Encrypt(keys.publicKey, cc.MakeCKKSPackedPlaintext(weights))

    # 내장 함수: EvalInnerProduct
    ct_inner = cc.EvalInnerProduct(ciphertext, ct_weights, batch_size)
    inner = decrypt_vector(cc, keys.secretKey, ct_inner, 1, digits=None)[0]
    expected_inner = sum(a * b for a, b in zip(values, weights))

    print("x               :", values)
    print("w               :", weights)
    print(f"expected <x, w> : {expected_inner}")
    print(f"decrypted       : {inner:.10f}")
    print(f"error           : {abs(inner - expected_inner):.3e}")
    print(f"level           : {ct_inner.GetLevel()} (곱셈 1번만 level 소모, 회전은 소모 X)")


if __name__ == "__main__":
    main()
