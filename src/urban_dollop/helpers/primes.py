def primes(n):
    result = [1]
    known = []
    candidate = 2
    while len(result) < n:
        if all(candidate % p != 0 for p in known):
            result.append(candidate)
            known.append(candidate)
        candidate += 1
    return result


def prime(n):
    return primes(n)[-1]
