def primes(n):
    if n <= 1:
        return [1]
    result = [1]
    # upper bound on the nth prime: n*(ln(n) + ln(ln(n))) holds for n >= 6
    import math
    if n < 6:
        upper = 15
    else:
        upper = int(n * (math.log(n) + math.log(math.log(n)))) + 2
    sieve = bytearray([1]) * (upper + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(upper ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
    for p in range(2, upper + 1):
        if sieve[p]:
            result.append(p)
            if len(result) == n:
                break
    return result


def prime(n):
    return primes(n)[-1]
