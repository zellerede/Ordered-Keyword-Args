from orderedkwargs import orderedkwargs

@orderedkwargs
def define_record(record_name, *fields) :
    print "record: %s" % (record_name,)
    print "fields: %s" % (fields,)

define_record("Point", x="Int32", y="Int32")
define_record("Person", name="Text", salary="Number")
