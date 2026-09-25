from openfhe import *

# python 01_basics/01_context.py

# CKKS 파라미터 생성 및 CryptoContext 생성 예제

def main():

    # CKKS 파라미터 생성 -> 어떻게 설정할지
    parameters = CCParamsCKKSRNS()

    # 곱셈 깊이 -> 연산을 얼마나 할지
    parameters.SetMultiplicativeDepth(2)

    # scaling factor의 크기 -> ckks에서는 실수를 연산하는데 그러기 위해서는 실수를 정수처럼 연산해야한다 그러기 위해 곱해지는 아주 큰 수 ()안에 숫자는 비트수준 50이면 50비트
    parameters.SetScalingModSize(50)

    # SIMD slot 개수 설정 -> 한번에 여러개의 값을 암호와 할수 있는데 몇개까지 동시에 할지
    parameters.SetBatchSize(8)

    # CryptoContext 생성 -> 파라미터를 기반으로 암호화 컨텍스트를 생성
    cc = GenCryptoContext(parameters)

    print("CryptoContext created!")

    print("Ring dimension:",
          cc.GetRingDimension())


if __name__ == "__main__":
    main()