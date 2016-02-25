

	

def factorial(number):
	result = 1
	for i in range(1, number + 1):
		result = result*i
	print(result)
		

def mainloop():
	quit = False
	while quit != True:
		x = str(raw_input("Please enter a number or hit 'q' to quit: "))
		
		if x == "q":
			print("Goodbye!")
			quit = True
		elif x.isdigit() == False:
			print("Not a number!")
			quit = True

		elif x.isdigit() == True:
			x = int(x)
			factorial(x)
			#quit = True
	
mainloop()		
		
	
	
	


		