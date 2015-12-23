'''
A file format parser for Skype's "chatsync" files.
Format as described by kmn in http://www.hackerfactor.com/blog/index.php?/archives/231-Skype-Logs.html#c1066

As the format specification used is not official and incomplete, the parser is limited in what it can do.
It may fail on some files, and on other files will only be able to extract messages partially.

Copyright 2015, Konstantin Tretyakov.
MIT License.
'''

from struct import unpack, calcsize
from collections import namedtuple
from datetime import datetime
import warnings
import os.path
from glob import glob


class ScanException(Exception):
    def __init__(self, message):
        super(ScanException, self).__init__(message)


class FileHeader(namedtuple('FileHeader', 'signature timestamp data_size padding')):
    __format__ = '<5sII19s'
    def validate(self, scanner):
        if self.signature != 'sCdB\x07':
            raise ScanException("Error scanning header in %s. Invalid signature: %s." % (scanner.name, self.signature))
        if self.padding != '\x00'*19:
            warnings.warn("Header padding not all zeroes in %s." % scanner.name)        
            scanner.warnings += 1

Block = namedtuple ('Block', 'block_header block_data')

class BlockHeader(namedtuple('BlockHeader', 'data_size x type padding')):
    __format__ = '<III4s'
    def validate(self, scanner):
        if self.padding != '\x00'*4:
            warnings.warn("Block #%d header padding not all zeroes in %s." % (len(scanner.blocks) + 1, scanner.name))
            scanner.warnings += 1
        if self.type < 1 or self.type > 6:
            raise ScanException("Error scanning block #%d in %s. Type field value %d invalid." % (len(scanner.blocks) + 1, scanner.name, self.type))

Message = namedtuple('Message', 'header records')

class MessageHeader(namedtuple('MessageHeader', 'id x timestamp y data_size')):
    __format__ = '<5I'
    def validate(self, scanner):
        pass

Record = namedtuple('Record', 'n fields')

class Field(namedtuple('Field', 'type code value')):
    INT = 0
    TYPE1 = 1
    STRING = 3
    BLOB = 4
    END_OF_RECORD = 5
    TYPE6 = 6


class SkypeChatSyncScanner(object):
    def __init__(self, file_like_object, name=None):
        self.input = file_like_object
        self.name = name if name is not None else repr(self.input)

    def scan(self):
        size, self.file_header = self.scan_struct(FileHeader)
        self.timestamp = datetime.fromtimestamp(self.file_header.timestamp)
        self.warnings = 0
        self.blocks = []
        size, self.blocks = self.scan_sequence(self.scan_block, self.file_header.data_size)
        self.validate()
        
    def validate(self):
        if len(self.blocks) != 6:
            warnings.warn("Incorrect number of blocks (%d) read from %s." % (len(self.blocks), self.name))
            self.warnings += 1
        else:
            block_ids = [b.block_header.type for b in self.blocks]
            if sorted(block_ids) != range(1, 7):
                warnings.warn("Not all blocks 1..6 are present in %s." % self.name)
                self.warnings += 1
        block_6 = [b for b in self.blocks if b.block_header.type == 6]
        if len(block_6) != 1:
            raise ScanException("Block 6 not found, or more than one found in file %s." % self.name)
        
    def scan_sequence(self, method, nbytes, stop_at=lambda x: False):
        items = []
        remaining = nbytes
        while remaining > 0:
            size, item = method(remaining)
            items.append(item)
            remaining -= size
            if stop_at(item):
                break
        if remaining < 0:
            warnings.warn("Invalid data size detected during sequence parsing in %s." % self.name)
            self.warnings += 1
        return nbytes - remaining, items
        
    def scan_struct(self, cls):
        size = calcsize(cls.__format__)
        data = self.input.read(size)
        if len(data) != size:
            raise ScanException("Error while scanning %s in %s. File too short." % (cls.__name__, self.name))
        result = cls._make(unpack(cls.__format__, data))
        result.validate(self)
        return size, result
    
    def scan_block(self, nbytes):
        hsize, block_header = self.scan_struct(BlockHeader)
        dsize, block_data = self.scan_block_data(block_header)
        return hsize + dsize, Block(block_header, block_data)
        
    def scan_block_data(self, block_header):
        if block_header.type == 5:
            return self.scan_block_5_data(block_header)
        elif block_header.type == 6:
            return self.scan_block_6_data(block_header)
        else:
            return self.scan_block_1_data(block_header)
    
    def scan_block_1_data(self, block_header):
        return self.scan_sequence(self.scan_record, block_header.data_size)

    def scan_block_5_data(self, block_header):
        return block_header.data_size, [unpack('<4I', self.input.read(16)) for i in range(block_header.data_size/16)]

    def scan_block_6_data(self, block_header):
        return self.scan_sequence(self.scan_message, block_header.data_size)
        
    def scan_record(self, nbytes):
        signature = self.input.read(1)
        if (signature != 'A'):
            raise ScanException("Record expected to start with 'A' in %s." % self.name)
        n = ord(self.input.read(1))
        if n == 0:
            return 2, Record(n, [])
        else:
            size, fields = self.scan_sequence(self.scan_field, nbytes-2, lambda f: f.type == Field.END_OF_RECORD)
            return size + 2, Record(n, fields)
    
    def scan_field(self, nbytes):
        type = ord(self.input.read(1))
        if type == Field.INT:
            csize, code = self.scan_7bitint()
            vsize, value = self.scan_7bitint()
        elif type == Field.STRING:
            csize, code = self.scan_7bitint()
            vsize, value = self.scan_cstring()
        elif type == Field.BLOB:
            csize, code = self.scan_7bitint()
            vsize, value = self.scan_blob()
        elif type == Field.TYPE1:
            csize, code = self.scan_7bitint()
            vsize, value = 8, self.input.read(8)
        elif type == Field.END_OF_RECORD:
            csize, code = self.scan_7bitint()
            vsize, value = 0, 0
        elif type == Field.TYPE6:
            code = self.input.read(1)             # Seems to always be 0x08
            csize, oneortwo = self.scan_7bitint() # Seems to always be 1 or 2
            vsize = 1
            value = []
            for i in range(oneortwo):
                _vsize, v = self.scan_7bitint()
                vsize += _vsize
                value.append(v)
        else:
            raise ScanException("Field of unexpected type %d detected in %s." % (type, self.name))
        return csize + vsize + 1, Field(type, code, value)

    def scan_message(self, nbytes):
        hsize, header = self.scan_struct(MessageHeader)
        rsize, records = self.scan_sequence(self.scan_record, header.data_size)
        return hsize + rsize, Message(header, records)
    
    def scan_7bitint(self):
        result = 0
        coef = 1
        size = 0
        loop = True
        while loop:
            v = self.input.read(1)
            if (v == ''):
                raise ScanException("Error parsing 7 bit integer in %s. Unexpected end of file." % self.name)
            v = ord(v)
            if v & 0x80:
                v = v ^ 0x80
            else:
                loop = False
            result += v * coef
            coef <<= 7
            size += 1
        return size, result
            
    def scan_cstring(self):
        result = ''
        c = self.input.read(1)
        while c != '\x00' and c != '':
            result += c
            c = self.input.read(1)
        return len(result) + 1, result
    
    def scan_blob(self):
        sizesize, size = self.scan_7bitint()
        data = self.input.read(size)
        return sizesize + len(data), data
        

ConversationMessage = namedtuple('ConversationMessage', 'timestamp author text is_edit')

class SkypeChatSyncParser(object):
    def __init__(self, scanner):
        self.scanner = scanner
    
    def parse(self):
        self.timestamp = self.scanner.file_header.timestamp
        self.conversation = []
        self.errors = 0
        self.is_empty = False
        if (len(self.scanner.blocks) == 0 or len(self.scanner.blocks[0].block_data) == 0 or len(self.scanner.blocks[0].block_data[0].fields) == 0):
            self.is_empty = True
            return
        participants = self.scanner.blocks[0].block_data[0].fields[0].value
        participants = participants.split(';')[0]
        participant1, participant2 = [name[1:] for name in participants.split('/')]
        self.participants = [participant1, participant2]
        
        # Find the first message with two parts - there we'll be able to detect the ID of the author of the conversation
        first_valid_block = -1
        for i, msg in enumerate(self.scanner.blocks[2].block_data):
            if len(msg.records) > 1 and len(msg.records[1].fields) > 1:
                first_valid_block = i
                break
        if first_valid_block == -1:
            self.is_empty = True
            return
        user1_id = self.scanner.blocks[2].block_data[first_valid_block].records[1].fields[1].value
        for msg in self.scanner.blocks[2].block_data:
            if len(msg.records) < 2: 
                continue
            if len(msg.records[1].fields) < 3:
                continue
            user_id = msg.records[1].fields[1].value
            blob = msg.records[1].fields[2].value
            try:
                msg_start = blob.index('\x03\x02')
                msg_end = blob.index('\x00', msg_start+1)
                msg_text = blob[msg_start+2:msg_end]
                is_edit = False
            except:
                try:
                    msg_start = blob.index('\x03"')
                    msg_end = blob.index('\x00', msg_start+1)
                    msg_text = blob[msg_start+2:msg_end]
                    is_edit = True
                except:
                    continue
            try:
                self.conversation.append(ConversationMessage(msg.header.timestamp, participant1 if user_id == user1_id else participant2, unicode(msg_text, 'utf-8'), is_edit))
            except:
                self.errors += 1


def parse_chatsync_file(filename):
    '''
    Parses a given chatsync file.
    Throws an exception on any failure (which may happen even if the file is legitimate simply because we do not know all the details of the format).
    
    If succeeds, returns a SkypChatSyncParser object. Check out its "is_empty", "timestamp", "conversation" and "participants" fields.
    '''
    with open(filename, 'rb') as f:
        s = SkypeChatSyncScanner(f)
        s.scan()
        p = SkypeChatSyncParser(s)
        p.parse()
    return p


def parse_chatsync_profile_dir(dirname):
    '''
    Looks for all *.dat files in a Skype profile's chatsync/ dir,
    returns a list of SkypeChatParser objects for those files that could be parsed successfully.
    '''
    files = glob(os.path.join(dirname, "*", "*.dat"))
    results = []
    for f in files:
        try:
            results.append(parse_chatsync_file(f))
        except Exception, e:
            warnings.warn("Failed to parse file %s. Exception: %s" % (f, e.message))
    return results