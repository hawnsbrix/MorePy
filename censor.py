def censor(text, word):
	wordlength = len(word)
	censoredword = '*' * wordlength 
	
	wordlist = text.split()
	newlist = []
	
	for item in wordlist:
		if item == word:
			newlist.append(censoredword)
		else:
			newlist.append(item)
	print " ".join(map(str, newlist))
	return " ".join(newlist)
	

	
def mainloop():
	exit = False
	while exit != True:
		entertext = str(raw_input("Please enter a sentence: "))
		
		if entertext == "":
			print("You failed to enter a sentence!")
			exit = True
		else:
			enterword = str(raw_input("Ok, now please enter a word to censor from that sentence: "))
			if enterword == "":
				print("You failed to enter a word to censor!")
				exit = True
			else:
				censor(entertext, enterword)
				exit = True
			
	
mainloop()	