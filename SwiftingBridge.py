import sys
import subprocess
from os import devnull

out = None
f = None
definedTypes = []

def generateHeader(appPath, appName):
    if appPath[-1:] == "/":
        appPath = appPath[:-1]
    
    if appPath[-4:] != ".app":
        print "Invalid application path"
        exit()
    
    FNULL = open(devnull, "w")

    sdef = subprocess.Popen(["sdef", appPath], stdout=subprocess.PIPE)
    sdp = subprocess.Popen(["sdp", "-fh", "--basename", appName], stdin=sdef.stdout, stderr=FNULL)
    sdp.communicate()

def isComment(line):
    if line[:2] == "//":
        out.write(line)
        return True

    elif line[:2] == "/*":
        try:
            out.write(line[line.index("/*"):line.index("*/")+2])

        except ValueError:
            out.write(line[line.index("/*"):])


        while not "*/" in line:
            line = f.readline()
            out.write(line)

        return True

def isImport(line):
    if line[:7] == "#import":
        frameworkName = line[9:line.index("/")]
        out.write("import " + frameworkName + "\n")
        return True

def isEnum(line):
    if line[:4] == "enum":
        enumName = line[5:line.index(" {")]
        out.write("@objc enum " + enumName + ": {\n")
        print "Warning: Must give type to enum " + enumName

        while not "};" in line:
            line = f.readline()
            line = line.replace("'", '"') #replace single quotes with double quotes
            line = line.replace(",", "") #remove trailing commas
            if " = " in line:
                out.write("\tcase ")
                out.write(line[1:])
            else:
                out.write(line)

        return True

def isInterface(line):
    global definedTypes
    if line[:10] == "@interface":
        interfaceName = line[11:line[11:].index(" ") + 11]

        out.write("@objc protocol " + interfaceName)
        try:
            super = line[line.index(":")+2:-1]
            if super in definedTypes:
                out.write(": " + super)
        except ValueError:
            super = None

        out.write(" {\n")
        
        if interfaceName in definedTypes:
            print "Warning: protocol for type '" + interfaceName + "' defined multiple times"
        
        definedTypes.append(interfaceName)
        
        line = f.readline()
        while not "@end" in line:
            handleLine(line)
            line = f.readline()
        
        out.write("}\n")

        if super != "SBApplication": #Assume everything else inherits from SBObject
            out.write("extension SBObject: " + interfaceName + "{}\n")

        else:
            out.write("extension SBApplication: " + interfaceName + "{}\n")

        return True

def parseType(type):
    type = type.rstrip("* ")
    type = escapedName(type)
    
    typeDict = {
                "id":                   "AnyObject",
                "BOOL":                 "Bool",
                "bool":                 "CBool",
                "char":                 "CChar",
                "signed char":          "CChar",
                "unsigned char":        "CUnsignedChar",
                "short":                "CShort",
                "unsigned short":       "CUnsignedShort",
                "int":                  "CInt",
                "unsigned int":         "CUnsignedInt",
                "long":                 "CLong",
                "unsigned long":        "CUnsignedLong",
                "long long":            "CLongLong",
                "unsigned long long":   "CUnsignedLongLong",
                "wchar_t":              "CWideChar",
                "char16_t":             "CChar16",
                "char32_t":             "CChar32",
                "float":                "CFloat",
                "double":               "CDouble"
    }
    
    try:
        return typeDict[type]

    except KeyError:
        return type

def escapedName(name):
    
    #Objective-C escaped keywords end in _
    #We must un-escape them first
    if name[-1:] == "_":
        name = name[:-1]
    
    reservedWords = ["as", "in", "for", "class", "deinit", "enum", "extension", "func", "import", "init", "internal", "let", "operator", "private", "protocol", "public", "static", "struct", "subscript", "typealias", "var", "break", "case", "continue", "default", "do", "else", "fallthrough", "for", "if", "in", "return", "switch", "where", "while", "as", "dynamicType", "false", "is", "nil", "self", "Self", "super", "true", " associativity", "convenience", "dynamic", "didSet", "final", "get", "infix", "inout", "lazy", "left", "mutating", "none", "nonmutating", "optional", "override", "postfix", "precedence", "prefix", "Protocol", "required", "right", "set", "Type", "unowned", "weak", "willSet"]
    
    if name in reservedWords:
        name = "`" + name + "`"
    
    return name

def isProperty(line):
    if line[:9] == "@property":
        typeIndex = 10
        readonly = False
        
        try:
            attrs = line[line.index("(")+1:line.index(")")] #TODO: Split by ", "
            typeIndex = line.index(")") + 2
    
            #TODO: Anything but this
            #not proud of this, but it works
            attrs.index("readonly") #if this throws a ValueError, then the next line won't run
            readonly = True
            
        except ValueError:
            attrs = None

        nameIndex = line.rfind(" ")
        name = line[nameIndex + 1:]

        #handle pointers
        if name[0] == "*":
            name = name[1:]

        type = line[line[:nameIndex].rfind(" ")+1:nameIndex]
        type = parseType(type)

        out.write("\toptional var " + name + ": " + type + " {get")

        if readonly:
            out.write("}\n")

        else:
            out.write(" set}\n")

        return True

def isFunction(line):
    if line[:3] == "- (":

        returnTypeEnd = line.index(")")
        returnType = line[3:returnTypeEnd]
        returnType = parseType(returnType)
        
        line = line[returnTypeEnd + 2:]
        
        inparams = line.split(":")
        funcName = inparams.pop(0)
        outparams = []
        
        
        for param in inparams:
            type = param[param.index("(")+1:param.index(")")]
            param = param[len(type)+2:]


            type = parseType(type)
            
            name = escapedName(param.split(" ")[0])
        
            outparams.append((name, type))

        out.write("\toptional func " + funcName + "(")
        
        if len(outparams) > 0:
            (param, type) = outparams.pop(0)
            out.write(param + ": " + type) #handles that pesky comma issue
            
            for (param, type) in outparams:
                out.write(", " + param + ": " + type)
                    
        if returnType != "void":
            out.write(") -> " + returnType + "\n")
                      
        else:
            out.write(")\n")

        return True

def isEmptyLine(line):
    if line.rstrip() == "":
        return True

def isJunkLine(line):
    if line[:6] == "@class":
        return True

    if line[:12] == "typedef enum":
        return True

def handleLine(line):
    line = line.replace("'", '"') #replace single quotes with double quotes
    line = line.lstrip() #remove whitespace
    statements = line.split(";") #in case of statements (including code w/ comments) on single line

    
    if not isComment(statements[0]):
        if not isImport(statements[0]):
            if not isEnum(statements[0]):
                if not isInterface(statements[0]):
                    if not isProperty(statements[0]):
                        if not isFunction(statements[0]):
                            if not isEmptyLine(statements[0]):
                                if not isJunkLine(statements[0]):
                                    print "Here there be dragons:"
                                    print line

    #handle any extra statements in same line
    if len(statements) > 1:
        handleLine(statements[1])


if len(sys.argv) <= 1:
    appPath = raw_input("Application path: ")
    appName = raw_input("Application name: ")

elif len(sys.argv) == 3:
    appPath = sys.argv[1]
    appName = sys.argv[2]

else:
    print "Invalid number of arguments"

generateHeader(appPath, appName)
out = open(appName + ".swift", "w")


f = open(appName + ".h")

#this allows handleLine to process multiple lines in a single call
lastLine = f.readline()
while lastLine != "":
    handleLine(lastLine)
    lastLine = f.readline()

f.close()
out.close()