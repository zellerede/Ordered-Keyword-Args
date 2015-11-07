# Ordered Keyword Args for Python

<i>(forked project, main idea and implementation is due to clayslab).</i>

Normally, Python doesn't preserve the order of keyword arguments passed to a function. That’s because it uses a dictionary to pass the arguments, and Python’s dictionary doesn’t remember the order in which elements are added.

That’s a problem in certain situations. For instance, if you want to define data models for serialization:

    def define_record(record_name, **kwargs) :
        print "record: %s" % (record_name,)
        print "fields: %s" % (kwargs.items(),)

    define_record("Point", x="Int32", y="Int32")

This is the output you get:

    record: Point
    fields: [('y', 'Int32'), ('x', 'Int32')]

As you can see, the order of the fields is wrong.

The orderedkwargs module solves this problem. Add the `@orderedkwargs` decorator, and you'll receive the keyword arguments as an OrderedDict object. Note that keyword arguments are received under the special argument `kwargs`, which has to be handled in the decorated method. <br>
Thus, kwargs being an OrderedDict, apart from the method header, <i> all other implementation can syntactically be identical</i> to the usual usage of ordinary `**kwargs`, only that the calling order is preserved!

    from orderedkwargs import orderedkwargs

    @orderedkwargs
    def define_record(record_name, kwargs) :
        print "record: %s" % (record_name,)
        print "fields: %s" % (kwargs.items(),)

    define_record("Point", x="Int32", y="Int32")

Now the output is:

    record: Point
    fields: (('x', 'Int32'), ('y', 'Int32'))


## How it works

The `@orderedkwargs` decorator wraps the function in an outer function that inspects the stack, parses the caller's byte code, and finds the order in which the keyword arguments are passed.

## Caveats

Because the `orderedkwargs` module depends on the internals of the Python VM, it is implementation specific. This particular code has been tested with CPython 2.7 and works only with that version. Also, don't use this in performance sensitive code. It is suitable for one-time tasks such as initialization at startup.
