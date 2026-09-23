from openfhe import *


def main():
    # CKKS 파라미터
    parameters = CCParamsCKKSRNS()

    parameters.SetMultiplicativeDepth(2)
    parameters.SetScalingModSize(50)
    parameters.SetBatchSize(8)

    # Crypto Context 생성
    cc = GenCryptoContext(parameters)

    # 사용할 기능 활성화
    cc.Enable(PKE)
    cc.Enable(KEYSWITCH)
    cc.Enable(LEVELEDSHE)

    # 키 생성
    keys = cc.KeyGen()

    # 평문
    values1 = [2.5]
    values2 = [3.5]

    plaintext1 = cc.MakeCKKSPackedPlaintext(values1)
    plaintext2 = cc.MakeCKKSPackedPlaintext(values2)

    # 암호화
    ciphertext1 = cc.Encrypt(keys.publicKey, plaintext1)
    ciphertext2 = cc.Encrypt(keys.publicKey, plaintext2)

    # 암호문 상태에서 계산
    ciphertext_result = cc.EvalAdd(
        ciphertext1,
        ciphertext2
    )

    # 복호화
    result = cc.Decrypt(
        keys.secretKey,
        ciphertext_result
    )

    result.SetLength(1)

    print("Input 1 :", values1[0])
    print("Input 2 :", values2[0])
    print("Result  :", result)


if __name__ == "__main__":
    main()