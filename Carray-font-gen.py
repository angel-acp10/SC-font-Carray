import freetype
import math
import unicodedata

class FontMetadata(object):
    def __init__(self, input_file):
        raw_rg_s, raw_rg_e, raw_str = self.ReadInputFile(self, input_file)
        self.rg_start, self.rg_end, self.rg_ch_info_idx = self.SortRanges(raw_rg_s, raw_rg_e, raw_str)
        self.line_height, self.max_ascent = self.CompFontMetrics(self)

    @staticmethod
    def ReadInputFile(self, inp_file):
        ''' 
        Reads 'input.txt' file to get the user introduced id. This id will 
        be used to store variable names of the output files.

        Reads 'input.txt' file to get the user introduced ranges as well as
        individual characters. Ranges are stored in 'range start' and 
        'range_end'. Individual characters are saved in 'string'.
        '''
        range_start, range_end = [], []
        string = ''

        f = open(inp_file, "r")
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
                self.id = line

            elif line.find('<file>=')!=-1:
                line = line.replace('<file>=','')
                self.font_file = line 
            
            elif line.find('<size>=')!=-1:
                line = line.replace('<size>=','')
                self.font_size = int(line)

            #range format example could be '[0x0120,0x3A3]' (without '')
            elif line[0]=='[' and line[-1]==']' and line.find(',')!=-1: 
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

        return(range_start, range_end, string)

    @staticmethod
    def SortRanges(raw_rg_s, raw_rg_e, raw_str):

        #once we have 'range_start', 'range_end' and 'string', let's include all
        #unicode codes into buff_list
        buff_list = []
        
        #include ranges
        for s, e in zip(raw_rg_s, raw_rg_e):
            for uc_idx in range(s,e+1):
                buff_list.append(uc_idx)
        
        #and the strings
        for char in raw_str:
            buff_list.append(ord(char))

        #remove duplicates unicode indexes
        buff_list = list(set(buff_list)) 
        
        #sorts the list
        buff_list.sort() 

        #sweep the entire buffer and find all its new ranges
        rg_start = [buff_list[0]]
        rg_end = [buff_list[0]]
        rg_ch_info_idx = [0]
        for i in range(len(buff_list)-1):
            if buff_list[i]+1 == buff_list[i+1]:
                rg_end[-1] += 1
            else:
                rg_start.append(buff_list[i+1])
                rg_end.append(buff_list[i+1])
                rg_ch_info_idx.append(i+1)
        
        return(rg_start, rg_end, rg_ch_info_idx)

    def GetFullStr(self):
        #put all characters in a single string
        char_buf = ''
        for s,e in zip(range(len(self.rg_start)), range(len(self.rg_end))):
            for c in range(self.rg_start[s], self.rg_end[e]+1):
                char_buf += chr(c) 
        
        return(char_buf)

    @staticmethod
    def CompFontMetrics(self):

        char_buf = self.GetFullStr()

        #compute max key metrics of the font
        font = Font(self.font_file, self.font_size)
        line_height, max_ascent = font.max_font_metrics(char_buf)
        return(line_height, max_ascent)



class Font(object):
    def __init__(self, font_file, size):
        self.face = freetype.Face(font_file)
        self.face.set_pixel_sizes(0, size)
        self.space_width = self.get_space_width(self)
        self.kern_width = self.get_fix_kern_width(self)

    def char_metrics(self, char):
        self.face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO )
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

    @staticmethod
    def get_space_width(self): #
        self.face.load_char('.', freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO )
        return self.face.glyph.bitmap.width

    @staticmethod
    def get_fix_kern_width(self):
        return math.ceil(self.get_space_width(self)/3)

class CharMetadata:
    def __init__(self, ch, width, height, y_offset, bitmap_idx):
        self.ch = ch
        self.width = width
        self.height = height
        self.y_offset = y_offset
        self.bitmap_idx = bitmap_idx

class GenerateOutputFile(object):
    def __init__(self, input_file):
        font_info = FontMetadata(input_file)
        font = Font(font_info.font_file, font_info.font_size)

        self.c_file = font_info.id + '.c'
        self.h_file = 'mcFont.h'
        self.WriteSrc(font, font_info)

        self.WriteHdr()
    
    def WriteSrc(self, font, font_info):
        f = open(self.c_file, "w+")

        f.write('#include "' + self.h_file + '"\r\n\r\n')
 
        f.write("static const uint8_t bitmap[] = {\r\n")

        char_buf = font_info.GetFullStr()

        #write bitmap into c file and save char metadata 
        char_info = []
        byte_idx = 0
        for c in char_buf:
            bitmap = font.get_bitmap(c)

            ascent, descent = font.char_metrics(c)
            y_offset = font_info.max_ascent - ascent

            # The space width generated by default is not correct,
            # so it is computed independently
            if c == ' ':
                char_info.append( CharMetadata( c, font.space_width, bitmap.rows, y_offset, byte_idx) )
            else:
                char_info.append( CharMetadata( c, bitmap.width, bitmap.rows, y_offset, byte_idx) )

            width_bytes = math.ceil(bitmap.width/8) # in bytes
            if c == '"':
                f.write( '\t// "\\' + c + '" ' + "U+{:04x}".format(ord(c))  + '\r\n')
            else:
                f.write( '\t// "' + c + '" ' + "U+{:04x}".format(ord(c))  + '\r\n')
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
        f.write("};\r\n\r\n")

        #print char metadata into c file
        f.write('static const ch_info_t ch_info[] = {\r\n')
        for c in char_info:
            f.write('\t{.bitmap_idx = ' + str(c.bitmap_idx) + ',')
            f.write('\t.y_offset = ' + str(c.y_offset) + ',')
            f.write('\t.w = ' + str(c.width) + ',')
            f.write('\t.h = ' + str(c.height) +'},')
            if c == '"':
                f.write( '\t// "\\' + c.ch + '" ' + "U+{:04x}".format(ord(c.ch))  + '\r\n')
            else:
                f.write( '\t// "' + c.ch + '" ' + "U+{:04x}".format(ord(c.ch))  + '\r\n')
        f.write('};\r\n\r\n')

        #print font data into c file
        f.write('static const uc_range_t uc_range[] = {\r\n')
        for s, e, ci_idx in zip(font_info.rg_start, font_info.rg_end, font_info.rg_ch_info_idx):
            f.write('\t{.start = ' + str(s) + ',')
            f.write('\t.end = ' + str(e) + ',')
            f.write('\t.ch_info_idx = ' + str(ci_idx) + '},')
            f.write('\t// [' + "U+{:04x}".format(s) + ' - ' + "U+{:04x}".format(e) + ']\r\n')
        f.write('};\r\n\r\n')

        #print the font structure
        f.write('mcFont_t ' + font_info.id + ' = {\r\n')
        f.write('\t.line_height = ' + str(font_info.line_height) + ',\r\n')
        f.write('\t.fix_kern = ' + str(font.kern_width) + ',\r\n')
        f.write('\t.uc_rg = uc_range,\r\n')
        f.write('\t.ch_info = ch_info,\r\n')
        f.write('\t.bm = bitmap,\r\n')
        f.write('};\r\n')

        f.close()

    def WriteHdr(self):
        f = open(self.h_file, "w+")
        f.write('#ifndef _MC_FONT_C_\r\n')
        f.write('#define _MC_FONT_C_\r\n\r\n')

        f.write('#include <stdint.h>\r\n\r\n')

        f.write('typedef struct{\r\n')
        f.write('\tuint16_t bitmap_idx;\r\n')
        f.write('\tuint8_t y_offset;\r\n')
        f.write('\tuint8_t w;\r\n')
        f.write('\tuint8_t h;\r\n')
        f.write('}ch_info_t;\r\n\r\n')

        f.write('typedef struct{\r\n')
        f.write('\tuint16_t start;\r\n')
        f.write('\tuint16_t end;\r\n')
        f.write('\tuint16_t ch_info_idx;\r\n')
        f.write('}uc_range_t;\r\n\r\n')

        f.write('typedef struct{\r\n')
        f.write('\tuint8_t line_height;\r\n')
        f.write('\tuint8_t fix_kern;\r\n')
        f.write('\tconst uc_range_t* uc_rg;\r\n')
        f.write('\tconst ch_info_t* ch_info;\r\n')
        f.write('\tconst uint8_t* bm;\r\n')
        f.write('}mcFont_t;\r\n\r\n')

        f.write('#endif\r\n')
        f.close()
        
              
if __name__ == '__main__':
    
    output = GenerateOutputFile('input.txt')
