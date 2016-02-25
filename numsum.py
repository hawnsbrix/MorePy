def digit_sum(numberstoadd):
	result = sum(int(x) for x in str(numberstoadd))
	return result

print digit_sum(12345)
print digit_sum(556677)
