from orderedkwargs import orderedkwargs

@orderedkwargs
def define_record(name, *fields) :
    print "record: %s" % (name,)
    for field_name, field_type in fields :
        print "  field %s: %s" % (field_name, field_type)
    print ""

define_record("Point", x=int, y=int)
define_record("Person", name=unicode, salary=float)
