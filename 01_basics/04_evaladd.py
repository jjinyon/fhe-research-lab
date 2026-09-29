
from openfhe import *

# python 01_basics/04_evaladd.py

def main():
    # 1. CKKS 파라미터 생성
    parameters = CCParamsCKKSRNS()
    parameters.SetMultiplicativeDepth(2)
    parameters.SetScalingModSize(50)
    parameters.SetBatchSize(8)

    # 2. CryptoContext 생성
    cc = GenCryptoContext(parameters)

    # 3. 암호 시스템 기능 활성화
    cc.Enable(PKESchemeFeature.PKE)
    cc.Enable(PKESchemeFeature.KEYSWITCH)
    cc.Enable(PKESchemeFeature.LEVELEDSHE)

    # 4. 키 생성
    keys = cc.KeyGen()

    # 5. 두 개의 원본 벡터 생성
    values1 = [1.0, 2.0, 3.0, 4.0]
    values2 = [10.0, 20.0, 30.0, 40.0]

    # 6. 두 벡터를 CKKS 평문으로 인코딩
    plaintext1 = cc.MakeCKKSPackedPlaintext(values1)
    plaintext2 = cc.MakeCKKSPackedPlaintext(values2)

    # 7. 두 평문을 각각 암호화
    ciphertext1 = cc.Encrypt(keys.publicKey, plaintext1)
    ciphertext2 = cc.Encrypt(keys.publicKey, plaintext2)

    # 8. 암호문 상태에서 덧셈 수행
    ciphertext_sum = cc.EvalAdd(ciphertext1, ciphertext2)

    # 9. 결과 암호문 복호화
    decrypted = cc.Decrypt(keys.secretKey, ciphertext_sum)

    # 10. 복호화 결과의 출력 길이 설정
    decrypted.SetLength(len(values1))

    # 11. 결과 확인
    decrypted_values = decrypted.GetRealPackedValue()

    print("Original values 1:", values1)
    print("Original values 2:", values2)
    print("Expected sum:", [
        a + b for a, b in zip(values1, values2)
    ])
    print("Decrypted sum:", decrypted_values)


if __name__ == "__main__":
    main()