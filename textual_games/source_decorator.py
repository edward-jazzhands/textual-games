
def called_by(*source_methods):
    """Decorator to mark either the calling function or the originator of a message.
    Can accept multiple source methods.

    ### Usage:
    @called_by(ClassName.method, some_func_foo, otherclass.foo)
    
    This achieves two goals:
    1) Allows for jump-clicking to the source of a message or a calling function.
    2) Validates that the 'source' method exists."""

    def decorator(func):
        return func
    return decorator

    # NOTE: There's no need for any validation here. If a source method is not found,
    # Python will raise an AttributeError. That is the validation.
