import freetype
import math
import unicodedata


class InputFile(object):
    def __init__(self, file_name):
        self.file_name = file_name

    def GetFontParam(self):
        ''' Reads 'input-txt' file to get the user introduced id. This id will 
            be used to store variable names of the output files.'''
        f = open(self.file_name, "r")
        line = f.readline()
        while line:
            line = line.strip()
            if line=='' or line[0]=='#':
                line = f.readline()
                continue

            line = line.replace(' ','')
            line = line.replace('\t', '')
            if line.find('<id>=')!=-1:
                line = line.replace('<id>=','')
                id = line

            elif line.find('<file>=')!=-1:
                line = line.replace('<file>=','')
                font_file = line 
            
            elif line.find('<size>=')!=-1:
                line = line.replace('<size>=','')
                font_size = int(line)

            line = f.readline()
        f.close()

        return(id, font_file, font_size)

    def GetUnicodeRanges(self):
        ''' Reads 'input.txt' file to get the user introduced ranges as well as
             individual characters. Ranges are stored in 'range start' and 
             'range_end'. Individual characters are saved in 'string'. '''
        range_start, range_end = [], []
        string = ''
        f = open(self.file_name, "r")
        line = f.readline()
        while line:
            line = line.strip()
            if line=='' or line[0]=='#':
                line = f.readline()
                continue
            line = line.replace(' ','')
            line = line.replace('\t', '')
            #range format example could be '[0x0120,0x3A3]' (without '')
            if line[0]=='[' and line[-1]==']' and line.find(',')!=-1: 
                line = line.strip('[')
                line = line.strip(']')
                rg = line.split(',',1)
                rg = [int(i,0) for i in rg]
                range_start.append(rg[0])
                range_end.append(rg[1])

            #string format example could be '"abcfu/*iyker"' (without '')
            elif line[0]=='"' and line[-1]=='"':
                string += line.strip('"')
            
            line = f.readline()
        f.close()

        #once we have 'range_start', 'range_end' and 'string', let's include all
        #unicode codes into buff_list
        buff_list = []
        
        #include ranges
        for start, end in zip(range_start, range_end):
            for uc_index in range(start,end+1):
                buff_list.append(uc_index)
        
        #and the strings
        for char in string:
            buff_list.append(ord(char))

        #remove duplicates codes
        buff_list = list(set(buff_list)) 
        
        #sorts the list
        buff_list.sort() 

        #sweep the entire buffer and find all its new ranges
        out_rg_start = [buff_list[0]]
        out_rg_end = [buff_list[0]]
        for i in range(len(buff_list)-1):
            if buff_list[i]+1 == buff_list[i+1]:
                out_rg_end[-1] += 1
            else:
                out_rg_start.append(buff_list[i+1])
                out_rg_end.append(buff_list[i+1])
        
        return(out_rg_start, out_rg_end)


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

    def max_font_metrics(self, text):
        max_ascent = 0
        max_descent = 0
        for char in text:
            ascent, descent = self.char_metrics(char)
            max_ascent = max(max_ascent, ascent)
            max_descent = max(max_descent, descent)
        font_height = max_ascent + max_descent
        return(font_height, max_ascent)

    def get_bitmap(self, char):
        self.face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO )
        return(self.face.glyph.bitmap)

class CharMetadata:
    def __init__(self, width, height, y_offset, map_idx):
        self.width = width
        self.height = height
        self.y_offset = y_offset
        self.map_idx = map_idx
    
class FontMetadata:
    def __init__(self, line_height, line_gap):
        self.line_height = line_height
        self.line_gap = line_gap

class OutputFile(object):
    def __init__(self, id):
        self.id = id
        #self.uc_ranges = ranges



              
if __name__ == '__main__':
    #get parameters from 'input.txt' file
    input = InputFile('input.txt')
    id, font_file, font_size = input.GetFontParam()
    range_start, range_end = input.GetUnicodeRanges()

    #put all characters in a single string
    char_buf = ''
    for s,e in zip(range(len(range_start)), range(len(range_end))):
        for c in range(range_start[s],range_end[e]+1):
            char_buf += chr(c) 

    #compute max key metrics of the font
    font = Font(font_file, font_size)
    line_height, max_ascent = font.max_font_metrics(char_buf)
    
    #fill the font metadata
    font_info = FontMetadata(line_height,2)
    
    f = open('output.c', "w+")
 
    f.write("static const uint8_t glyph_bitmap[] = {\r\n")

    #fill the char metadata
    char_info = []
    byte_idx = 0
    for c in char_buf:
        bitmap = font.get_bitmap(c)

        ascent, descent = font.char_metrics(c)
        y_offset = max_ascent - ascent
        char_info.append( CharMetadata(bitmap.width, bitmap.rows, y_offset, byte_idx) )

        width_bytes = math.ceil(bitmap.width/8) # in bytes
        f.write( '// "' + c + '"\r\n')
        for y in range(bitmap.rows):
            f.write('\t')
            for x in range(width_bytes):
                byte = bitmap.buffer[y*bitmap.pitch + x] #bitmap.pitch is the number of bytes per row used in the buffer
                print( format( byte, '#010b')+', ', end = '' )
                f.write( format( byte, '#010b')+', ' )
                byte_idx += 1
            print('\n', end = '' )
            f.write('\r\n')
        print('\n', end = '' )
        f.write('\r\n')

    f.write("}")


