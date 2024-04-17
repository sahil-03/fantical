if __name__ == '__main__':
    with open('../emoji.txt', 'r') as f: 
        lines = f.readlines()
    
    elist = '['
    for l in lines: 
        temp = l.split('(')[1]
        elist += f'\'{temp[0]}\', '
    elist += ']'
    print(elist)
    


