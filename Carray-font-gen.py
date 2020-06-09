import freetype
import math
face = freetype.Face("helvetica.ttf")
size = 10

face.set_pixel_sizes( 0, size )

class Metadata:
    def __init__(self, char, width, height, y_offset):
        self.char = char
        self.width = width
        self.height = height
        #each char is placed from the top left corner, y_offset sets the vertical offset from that corner
        self.y_offset = y_offset 

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

            

font = Font('helvetica.ttf', 8)
font.write_to_C_file('abcdefghijklmnopqrstuvwxyz')
        
