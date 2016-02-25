def censor(text, word):
	textlist = text.split()
	censored_text = []
	for element in textlist:
		if element == word:
			element = "*" * len(word)
			censored_text.append(element)
		else:
			censored_text.append(element)	
	return " ".join(censored_text)

def input_check(n):
	n_split = n.split()
	for i in n_split:
		if i.isalpha() == False and i != " ":
			print "Wrong input."
			return False
		elif n == " ":
			print "Wrong input."
			return False
		else:
			return True

def main():
	quit = False
	print
	print 'Censor.'
	print

	while quit != True:
		input1 = raw_input('Enter your text or q to exit :')
		if input1 == 'q':
			print "***."
			quit = True
		elif input_check(input1) == True:
			input2 = raw_input('Enter the word to censor or q to exit :')
			if input2 == 'q':
				print "***."
				quit = True
			elif input_check(input2) == True:
				print
				print "Censored version :", censor(input1, input2)
				print 
			else:
				print 'Try again.'
main()