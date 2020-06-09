import freetype
import math
import unicodedata

face = freetype.Face("helvetica.ttf")
size = 10

face.set_pixel_sizes( 0, size )

class Metadata:
    def __init__(self, unicode):
        self.unicode = unicode

    def setParameters(width, height, y_offset):
        self.width = width
        self.height = height
        #each char is placed from the top left corner, y_offset sets the vertical offset from that corner
        self.y_offset = y_offset 

class DataInput:
    def __init__(self):
        self.range_start, self.range_end = [], []
        self.string = ''

        f = open("input.txt", "r")
        line = f.readline()
        while line:
            line = line.strip()
            line = line.replace(' ','')
            line = line.replace('\t', '')

            if line[0]=='[' and line[-1]==']' and line.find(',')!=-1:
                line = line.strip('[')
                line = line.strip(']')
                rg = line.split(',',1)
                rg = [int(i,0) for i in rg]
                self.range_start.append(rg[0])
                self.range_end.append(rg[1])

            elif line[0]=='"' and line[-1]=='"':
                self.string += line.strip('"')
            
            line = f.readline()
        f.close()

        print(self.range_start)
        print(self.range_end)
        print(self.string)

        self.Sort()
        self.FindRanges()

    def Sort(self):
        self.buff_list = []
        
        #save all the unicode indexes within the introduced range in a buffer list
        for start, end in zip(self.range_start, self.range_end):
            for uc_index in range(start,end+1):
                self.buff_list.append(uc_index)
        
        for char in self.string:
            self.buff_list.append(ord(char))

        #removes duplicates
        self.buff_list = list(set(self.buff_list)) 
        print(self.buff_list)

        self.buff_list.sort() #sorts the list
        print(self.buff_list)

    def FindRanges(self):
        fr_start = [self.buff_list[0]]
        fr_end = [self.buff_list[0]]
        for i in range(len(self.buff_list)-1):
            if self.buff_list[i]+1 == self.buff_list[i+1]:
                fr_end[-1] += 1
            else:
                fr_start.append(self.buff_list[i+1])
                fr_end.append(self.buff_list[i+1])
        
        print(fr_start)
        print(fr_end)






        



'''
class Font(object):
    def __init__(self, filename, size):
        self.face = freetype.Face(filename)
        self.face.set_pixel_sizes(0, size)

    def char_metrics(self, char):
        self.face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO )
        #width = self.face.glyph.bitmap.width
        height = self.face.glyph.bitmap.rows

        top = self.face.glyph.bitmap_top
        descent = max(0, height - top)
        ascent = max(0, max(top, height) - descent)
        return(ascent, descent) 

    def max_char_metrics(self, text):
        max_ascent = 0
        max_descent = 0
        for char in text:
            ascent, descent = self.char_metrics(char)
            max_ascent = max(max_ascent, ascent)
            max_descent = max(max_descent, descent)
        font_height = max_ascent + max_descent
        return(font_height, max_ascent)

    def write_to_C_file(self, text):
        metadata = []
        self.font_height, self.max_ascent = self.max_char_metrics(text)
        
        for char in text:
            self.face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO )

            buffer = self.face.glyph.bitmap.buffer
            height = self.face.glyph.bitmap.rows
            width_bits = self.face.glyph.bitmap.width
            width = math.ceil(width_bits/8) # in bytes
            real_width = self.face.glyph.bitmap.pitch  # in bytes
            ascent, descent = self.char_metrics(char)
            y_offset = self.max_ascent - ascent

            metadata.append( Metadata(char, width_bits, height, y_offset) )

            for y in range(height):
                for x in range(width):
                    byte = buffer[y*real_width + x]
                    print( format( byte, '#010b')+', ', end = '' )
                print('\n', end = '' )
            print('\n', end = '' )

            f_height = self.font_height
            # full slot

            while y_offset:
                for i in range(width):
                    print( format( 0, '#010b')+', ', end = '' )
                print('\n', end = '' )
                y_offset -= 1
                f_height -= 1

            for y in range(height):
                for x in range(width):
                    byte = buffer[y*real_width + x]
                    print( format( byte, '#010b')+', ', end = '' )
                print('\n', end = '' )
                f_height -= 1

            while f_height:
                for i in range(width):
                    print( format( 0, '#010b')+', ', end = '' )
                print('\n', end = '' )
                f_height -= 1
            print('\n', end = '' )
            
        for char_info in metadata:
            print(str(char_info.char) + '--> w='+str(char_info.width) + '\th='+str(char_info.height) + '\tyoff='+str(char_info. y_offset) )
'''
            

#font = Font('helvetica.ttf', 8)
#font.write_to_C_file('abcdefghijklmnopqrstuvwxyz')
'''
c='ε'
c=ord(c)
print(c)
print(type(c))
'''

data = DataInput()
