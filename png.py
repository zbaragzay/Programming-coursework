
from zlib import decompress, crc32, compress
#import math

class PNG:
    def __init__(self):
        """"
        Initialize function create instance attributes and sets them to 0
        """
        self.data = b'' # Holds raw data of png file
        self.info = ''
        self.width = 0
        self.height = 0
        self.bit_depth = 0
        self.color_type = 0
        self.compress = 0
        self.filter = 0
        self.interlace = 0
        self.img = [] #Creates list to hold data as an array

    def load_file(self, file_name):
        """
        Loads a PNG file into the object by reading the file's bytes and storing them.
        Also sets the 'info' attribute to the file name.

        Arguments:
            file_name (str): The name of the file to load.
        """
        try:
            with open(file_name, 'rb') as f:
                self.data = f.read()
                self.info = file_name
        except FileNotFoundError:
            self.info = 'file not found'

    def valid_png(self):
        """
        Checks if the loaded data represents a valid PNG file.
        Verifies that the first 8 bytes match the PNG signature.

        Returns:
            bool: True if the file is a valid PNG, False otherwise.
        """
        signature = b'\x89PNG\r\n\x1a\n' #png signature

        if not self.data: #Checks if data attribute is empty
            return False

        return self.data[:8] == signature #Read the first 8 bytes and compare to PNG signature

    def read_header(self):
        """
        Reads the header chunk (IHDR) of the PNG file and extracts essential metadata.
        This function sets the width, height, bit depth, color type, compression method,
        filter method, and interlace method from the IHDR chunk.

            Raises:
                ValueError: If the file is not a valid PNG or the IHDR chunk is invalid.
        """
        if not self.valid_png(): #
            raise ValueError("Can't read header, Not a valid PNG file.")

        ihdr_start = 8
        ihdr_length = int.from_bytes(self.data[ihdr_start:ihdr_start+4]) #First 4 bytes after signature is chunk length
        ihdr_type = self.data[ihdr_start+4: ihdr_start+8] #Next 4 bytes is the chunk type

        if ihdr_type != b'IHDR':
            raise ValueError("IHDR chunk invalid.")

        ihdr_data = self.data[16:29]
#Next we extract the header fields and assign to attributes
        self.width = int.from_bytes(ihdr_data[0:4])
        self.height = int.from_bytes(ihdr_data[4:8])
        self.bit_depth = int.from_bytes(ihdr_data[8:9])
        self.color_type = int.from_bytes(ihdr_data[9:10])
        self.compress = int.from_bytes(ihdr_data[10:11])
        self.filter = int.from_bytes(ihdr_data[11:12])
        self.interlace = int.from_bytes(ihdr_data[12:13])

    def unfilter_1(self, row_data, bpp):
        """
        Reconstruct byte using filter type 1 (out)
        Arguments:
           row_data (bytes): The row data to unfilter.
           bpp (int): Bytes per pixel (typically 3 for RGB)         .
        Returns:
            list: The reconstructed row.
        """
        result = []
        for i in range(len(row_data)):
            left = result[i-bpp] if i>=bpp else 0 #For each byte we take the pixel that's 3 bytes to the left
            result.append((row_data[i] + left) %256)
        return result

    def unfilter_2(self, row_data, prev_row):
        """Reconstructs byte for filter type 2 (Up).
           Takes in row_data and prev_row(row above this one, row above first row is all 0s)
        """
        result = []
        for i in range(len(row_data)):
            above = prev_row[i] if prev_row else 0
            result.append((row_data[i] + above) % 256)
        return result

    def unfilter_3(self, row_data, prev_row, bpp):
        """Unfilter for filter type 3 (Average)."""
        result = []
        for i in range(len(row_data)):
            left = result[i - bpp] if i >= bpp else 0
            above = prev_row[i] if prev_row else 0
            avg = (left + above) // 2
            result.append((row_data[i] + avg) % 256)
        return result

    def unfilter_4(self, row_data, prev_row, bpp):
        """Unfilter for filter type 4 (Paeth)."""
        result = []
        for i in range(len(row_data)):
            left = result[i - bpp] if i >= bpp else 0
            above = prev_row[i] if prev_row else 0
            upper_left = prev_row[i - bpp] if i >= bpp and prev_row else 0

            p = left + above - upper_left
            pa = abs(p - left)
            pb = abs(p - above)
            pc = abs(p - upper_left)
            if pa <= pb and pa <= pc:
                predictor = left
            elif pb <= pc:
                predictor = above
            else:
                predictor = upper_left

            result.append((row_data[i] + predictor) % 256)
        return result

    def read_chunks(self):
        """
        Reads through the chunks following the IHDR chunk (including IDAT and IEND).
        Concatenates all IDAT chunks, decompresses the data, and stores the resulting image data.
        """
        if self.width == 0 or self.height == 0:
            raise ValueError("Header must be read before reading chunks.")

        offset = 33 #8 bytes for signature and 25 for IHDR
        compressed_data = b''

        while offset < len(self.data): #Loop through chunk extracting data
            chunk_length = int.from_bytes(self.data[offset:offset + 4], byteorder='big')
            chunk_type = self.data[offset+4:offset+8]
            chunk_data = self.data[offset + 8: offset + 8 + chunk_length]
            chunk_crc = self.data[offset+ chunk_length + 8: offset + 12 + chunk_length]

            if chunk_type == b'IDAT':
                compressed_data += chunk_data
            elif chunk_type == b'IEND':
                break
            offset += 8 + chunk_length + 4
        decompressed_data = decompress(compressed_data)
        self.img = self.process_data(decompressed_data)

    def process_data(self, decompressed_data):
        """
        reconstructs data using assigned filter type to each row
        :param decompressed_data:
        :return: processed image data in a list
        """

        img = []
        bpp = 3 #RGB images have 3 bpp(bytes per pixel)
        row_length = self.width * bpp

        offset = 0
        prev_row = None
        for i in range(self.height):
            filter_type = decompressed_data[offset] #The first byte of each row is the filter type
            offset += 1
            row_data = decompressed_data[offset:offset+row_length]
            offset += row_length

            if filter_type ==0:
                reconstructed_row = row_data
            elif filter_type ==1:
                reconstructed_row = self.unfilter_1(row_data, bpp)
            elif filter_type ==2:
                reconstructed_row = self.unfilter_2(row_data, prev_row)
            elif filter_type ==3:
                reconstructed_row = self.unfilter_3(row_data, prev_row, bpp)
            elif filter_type ==4:
                reconstructed_row = self.unfilter_4(row_data, prev_row, bpp)
            else:
                raise ValueError(f"unsupported filter type: {filter_type}")

            row = [reconstructed_row[j:j + bpp] for j in range(0, len(reconstructed_row), bpp)]
            img.append(row)
            prev_row = reconstructed_row #Update the prev row as it contains the 'above' byte when reconstructing bytes.
        return img

    def _to_bytes(self, integer, length):
        """Converts an integer to a byte array of a given length (big-endian)."""
        return integer.to_bytes(length, byteorder='big')

    def _create_chunk(self, chunk_type, chunk_data):
        """Creates a PNG chunk with length, type, data, and CRC."""
        length = len(chunk_data)
        # Convert length and CRC into byte arrays manually
        length_bytes = self._to_bytes(length, 4)
        # Calculate CRC (Cyclic Redundancy Check) using zlib's crc32
        crc = crc32(chunk_type + chunk_data) & 0xffffffff
        crc_bytes = self._to_bytes(crc, 4)

        # Construct the complete chunk (length + type + data + CRC)
        return length_bytes + chunk_type + chunk_data + crc_bytes

    def save_rgb(self, file_name, rgb_option):
        """
        Saves the specified color channel (red, green, or blue) as a grayscale PNG file.

        Arguments:
            file_name (str): The output PNG file name.
            rgb_option (int): The channel to save (1=red, 2=green, 3=blue).

        Returns:
            None
        """
        if rgb_option not in [1, 2, 3]:
            raise ValueError("Invalid rgb_option. Must be 1 (red), 2 (green), or 3 (blue).")
        if not self.img:
            raise ValueError("Image data is empty. Cannot save.")

        # Define the index for the selected color channel
        channel_index = rgb_option - 1

        # This will hold the new grayscale image data (with only one channel filled)
        channel_data = []

        # Loop over each row in the image
        for row in self.img:
            # This will hold the modified row where only one channel is non-zero
            modified_row = []

            # Loop over each pixel in the row, starting from the second byte to skip the filter byte
            for pixel in row:
                # Create a new pixel with the selected channel non-zero, others set to 0
                if rgb_option == 1:  # Red channel
                    modified_pixel = [pixel[0], 0, 0]  # Set Green and Blue to 0
                elif rgb_option == 2:  # Green channel
                    modified_pixel = [0, pixel[1], 0]  # Set Red and Blue to 0
                elif rgb_option == 3:  # Blue channel
                    modified_pixel = [0, 0, pixel[2]]  # Set Red and Green to 0

                # Append the modified pixel to the row
                modified_row.extend(modified_pixel)

            # Add the modified row to the image data
            channel_data.append(modified_row)

        # Now we need to prepare the data for the PNG file, with the requirements
        width_bytes = self.width.to_bytes(4, byteorder='big')
        height_bytes = self.height.to_bytes(4, byteorder='big')
        bit_depth = b'\x08'
        color_type = b'\x02'
        compression = b'\x00'
        filter_method = b'\x00'
        interlace = b'\x00'

        # Concatenate parts to form the IHDR chunk data
        ihdr_data = width_bytes + height_bytes + bit_depth + color_type + compression + filter_method + interlace
        ihdr_chunk = self._create_chunk(b'IHDR', ihdr_data)

        # Now handle the IDAT chunk: Compress the channel data and prepare it for storage.
        raw_data = b''.join(b'\x00' + bytes(row) for row in channel_data)  # Add filter byte (0) for each row
        compressed_data = compress(raw_data)

        # Create the IDAT chunk with the length of the compressed data
        idat_chunk = self._create_chunk(b'IDAT', compressed_data)

        # Create the IEND chunk (end of image)
        iend_chunk = self._create_chunk(b'IEND', b'')

        # Write the PNG file to disk
        with open(file_name, 'wb') as f:
            #Png signature remains the same
            f.write(b'\x89PNG\r\n\x1a\n')

            # Write the IHDR chunk
            f.write(ihdr_chunk)

            # Write the IDAT chunk
            f.write(idat_chunk)

            # Write the IEND chunk
            f.write(iend_chunk)