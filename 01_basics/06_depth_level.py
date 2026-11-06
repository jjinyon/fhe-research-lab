
import math

from openfhe import *

# python 01_basics/06_depth_level.py

def run(depth, num_squarings):
    print("=" * 60)
    print(f"MultiplicativeDepth = {depth}, 제곱 반복 횟수 = {num_squarings}")
    print("=" * 60)

    # 1. CKKS 파라미터 생성
    parameters = CCParamsCKKSRNS()
    parameters.SetMultiplicativeDepth(depth)
    parameters.SetScalingModSize(50)
    parameters.SetBatchSize(8)

    # 2. CryptoContext 생성
    cc = GenCryptoContext(parameters)

    # 3. 암호 시스템 기능 활성화
    cc.Enable(PKESchemeFeature.PKE)
    cc.Enable(PKESchemeFeature.KEYSWITCH)
    cc.Enable(PKESchemeFeature.LEVELEDSHE)

    # 4. 키 생성 + 곱셈용 재선형화 키 생성
    keys = cc.KeyGen()
    cc.EvalMultKeyGen(keys.secretKey)

    # 5. 원본 벡터 생성 (값이 너무 커지지 않도록 1 근처의 값 사용)
    values = [0.9, 1.0, 1.1, 1.2]

    # 6. 인코딩 + 암호화
    plaintext = cc.MakeCKKSPackedPlaintext(values)
    ciphertext = cc.Encrypt(keys.publicKey, plaintext)

    print(f"[step 0] x^1   level = {ciphertext.GetLevel()}, "
          f"scale = 2^{math.log2(ciphertext.GetScalingFactor()):.1f}")

    # 7. 제곱을 반복하면서 level / scale / 오차 관찰
    #    x -> x^2 -> x^4 -> x^8 -> ...
    expected = values[:]
    for step in range(1, num_squarings + 1):
        try:
            ciphertext = cc.EvalMult(ciphertext, ciphertext)
        except Exception as e:
            print(f"[step {step}] EvalMult 실패: {e}")
            print("  -> 설정한 곱셈 깊이를 초과해서 더 이상 곱셈할 수 없음")
            break

        expected = [v * v for v in expected]

        # 8. 복호화해서 실제 값과 비교
        try:
            decrypted = cc.Decrypt(keys.secretKey, ciphertext)
            decrypted.SetLength(len(values))
            decrypted_values = decrypted.GetRealPackedValue()
            max_error = max(abs(a - b) for a, b in zip(decrypted_values, expected))
        except Exception as e:
            print(f"[step {step}] Decrypt 실패: {e}")
            break

        print(f"[step {step}] x^{2 ** step:<3} level = {ciphertext.GetLevel()}, "
              f"scale = 2^{math.log2(ciphertext.GetScalingFactor()):.1f}, "
              f"max error = {max_error:.3e}")

    print()


def main():
    # depth 안에서 곱셈하는 경우: 정상 동작
    run(depth=3, num_squarings=3)

    # depth를 초과해서 곱셈하는 경우: 실패 또는 결과 깨짐
    run(depth=3, num_squarings=5)

    # depth를 늘리면 더 많이 곱할 수 있음 (대신 파라미터가 커져서 느려짐)
    run(depth=5, num_squarings=5)


if __name__ == "__main__":
    main()
