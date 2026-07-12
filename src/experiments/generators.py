def numeri():
    print("funzione iniziata")

    yield 1

    print("funzione finita")

    yield 2


gen = numeri()

print(type(gen))

print(next(gen))

def numbers():

    print("Start")

    for i in range(5):

        print(f"Sto producendo {i}")

        yield i

    print("Fine")


gen = numbers()
print(type(gen))
next(gen)
next(gen)