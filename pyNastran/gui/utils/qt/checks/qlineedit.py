import os
from typing import Tuple, Optional
from functools import wraps

QLINE_EDIT_BASIC = 'QLineEdit{background: white;}'
QLINE_EDIT_ERROR = 'QLineEdit{background: red;}'

def check_path(cell):
    """verifies that the path exists"""
    path, passed = check_name_str(cell)
    if not passed:
        return None, False

    if not os.path.exists(path):
        cell.setStyleSheet(QLINE_EDIT_ERROR)
        return None, False
    cell.setStyleSheet(QLINE_EDIT_BASIC)
    return path, True

def check_save_path(cell):
    """verifies that the path is savable..."""
    text, passed = check_name_str(cell)
    if not passed:
        return None, False
    return text, passed

#-------------------------------------------------------------------------------
def check_int(cell):
    """
    Colors the cell red if the integer is invalid

    Parameters
    ----------
    cell : QLineEdit()
        a PyQt/PySide object

    Returns
    -------
    value : int / None
        int : the value as a int
        None : is_passed=False
    is_passed : bool
        is this a valid integer
    """
    text = cell.text()
    try:
        value = int(text)
        cell.setStyleSheet("QLineEdit{background: white;}")
        return value, True
    except ValueError:
        cell.setStyleSheet("QLineEdit{background: red;}")
        return None, False

def check_positive_int_or_blank(cell):
    text = str(cell.text()).strip()
    if len(text) == 0:
        return None, True
    try:
        value = int(text)
    except ValueError:
        cell.setStyleSheet("QLineEdit{background: red;}")
        return None, False

    if value < 1:
        cell.setStyleSheet("QLineEdit{background: red;}")
        return None, False

    cell.setStyleSheet("QLineEdit{background: white;}")
    return value, True

#def check_float(cell):
    #text = cell.text()
    #try:
        #value = eval_float_from_string(text)
        #cell.setStyleSheet("QLineEdit{background: white;}")
        #return value, True
    #except ValueError:
        #cell.setStyleSheet("QLineEdit{background: red;}")
        #return None, False

def check_float(cell):
    """
    Colors the cell red if the float is invalid

    Parameters
    ----------
    cell : QLineEdit()
        a PyQt/PySide object

    Returns
    -------
    value : float / None
        float : the value as a float
        None : is_passed=False
    is_passed : bool
        is this a valid float
    """
    text = cell.text()
    value, is_valid = _check_float(text)
    if is_valid:
        cell.setStyleSheet("QLineEdit{background: white;}")
        return value, True
    else:
        cell.setStyleSheet("QLineEdit{background: red;}")
        return None, False

def _check_float(text: str) -> Tuple[Optional[str], bool]:
    """
    This is intended as a locale safe way to parse a float.
    It supports various types of floats.

    Example
    -------
    >>> _check_float('3.14')
    3.14, True
    >>> _check_float('2,557')
    2,557, True
    """
    value = None
    is_valid = False
    try:
        value = float(text)
        is_valid = True
    except ValueError:
        #'2,557'
        if ',' not in text:  # not valid
            pass
        elif '.' in text and ',' in text:  # might be valid; 1,234.56  -> 1.234,56
            # not supported
            pass
        else:
            text2 = text.replace(',', '.')
            value = float(text2)
            is_valid = True
    except:
        pass
    return value, is_valid

def check_float_ranged(cell, min_value=None, max_value=None,
                       min_inclusive=True, max_inclusive=True):
    """
    Colors the cell red if the float is invalid or the value is outside
    the range [min_value, max_value].

    Parameters
    ----------
    cell : QLineEdit()
        a PyQt/PySide object
    min_value / max_value : float / None
        float : the constraint is active
        None : the constraint is inactive
    min_inclusive / max_inclusive; bool; default=True
        flips [min_value, max_value] to:
          - (min_value, max_value)
          - [min_value, max_value)
          - (min_value, max_value]

    Returns
    -------
    value : float / None
        float : the value as a float
        None : is_passed=False
    is_passed : bool
        is this a valid float that meets the range requirements
    """
    value, is_passed = check_float(cell)
    if not is_passed:
        #print("failed %r" % value)
        return value, is_passed

    is_ranged = _is_ranged_value(
        value, min_value=min_value, max_value=max_value,
        min_inclusive=min_inclusive, max_inclusive=max_inclusive)

    color = 'white'
    if not is_ranged:
        value = None
        color = 'red'
    cell.setStyleSheet("QLineEdit{background: %s;}" % color)

    return value, is_ranged

def _is_ranged_value(value, min_value=None, max_value=None,
                     min_inclusive=True, max_inclusive=True):
    """
    Parameters
    ----------
    value : float
        float : the value as a float
    min_value / max_value : float / None
        float : the constraint is active
        None : the constraint is inactive
    min_inclusive / max_inclusive; bool; default=True
        flips [min_value, max_value] to:
          - (min_value, max_value)
          - [min_value, max_value)
          - (min_value, max_value]

    Returns
    -------
    is_ranged : bool
        is the value in range
    """
    is_ranged = True
    if min_value is not None:
        #print("min:")
        if min_inclusive:
            # ( is the goal
            if value < min_value:
                is_ranged = False
                #print('  min_exclusive, %s %s' % (value, min_value))
            #else:
                #print('  passed minA=%s' % value)
        else:
            # [ is the goal
            if value <= min_value:
                is_ranged = False
                #print('  min_inclusive, %s %s' % (value, min_value))
            #else:
                #print('  passed minB=%s' % value)
    #else:
        #print('no limit on min')

    if max_value is not None:
        #print("max:")
        if max_inclusive:
            # ] is the goal
            if value > max_value:
                #print('  max_exclusive, %s %s' % (value, max_value))
                is_ranged = False
            #else:
                #print('  passed maxA=%s' % value)
        else:
            # ) is the goal
            if value >= max_value:
                is_ranged = False
                #print('  max_inclusive, %s %s' % (value, max_value))
            #else:
                #print('  passed maxB=%s' % value)
    #else:
        #print('no limit on max')
    return is_ranged

#-------------------------------------------------------------------------------
def check_name_str(cell):
    """
    Verifies that the data is string-able.

    Parameters
    ----------
    cell : QLineEdit
        a QLineEdit containing a string.

    """
    cell_value = cell.text()
    try:
        text = str(cell_value).strip()
    except UnicodeEncodeError:
        cell.setStyleSheet("QLineEdit{background: red;}")
        return None, False

    if len(text):
        cell.setStyleSheet("QLineEdit{background: white;}")
        return text, True
    else:
        cell.setStyleSheet("QLineEdit{background: red;}")
        return None, False

def check_name_length(cell):
    """
    Verifies that the string has at least 1 non-whitespace character.

    Parameters
    ----------
    cell : QLineEdit
        a QLineEdit containing a string.
    """
    cell_value = cell.text()
    text = cell_value.strip()

    if len(text):
        cell.setStyleSheet("QLineEdit{background: white;}")
        return text, True
    else:
        cell.setStyleSheet("QLineEdit{background: red;}")
        return None, False

def check_format(cell):
    """
    Checks a QLineEdit string formatter

    Parameters
    ----------
    cell : QLineEdit
        a QLineEdit containing a string formatter like:
        {'%s', '%i', '%f', '%g', '%.3f', '%e'}

    Returns
    -------
    text : str / None
        str : the validated text of the QLineEdit
        None : the format is invalid
    is_valid : bool
        The str/None flag to indicate if the string formatter is valid
    """
    text = str(cell.text())
    text2, is_valid = check_format_str(text)

    if is_valid:
        cell.setStyleSheet("QLineEdit{background: white;}")
        return text2, True
    cell.setStyleSheet("QLineEdit{background: red;}")
    return None, False

def nocrash_str_bool(func):
    @wraps(func)
    def wrapper(_str):
        try:
            out = func(_str)
        except:
            #print('dont crash...')
            out = (_str, False)
        return out
    return wrapper

@nocrash_str_bool
def check_format_str(text: str) -> Tuple[str, bool]:
    """
    Checks a QLineEdit string formatter

    Parameters
    ----------
    text : str
        a QLineEdit containing a string formatter like:
        {'%s', '%i', '%f', '%g', '%.3f', '%e'}

    Returns
    -------
    text : str / None
        str : the validated text of the QLineEdit
        None : the format is invalid
    is_valid : bool
        The str/None flag to indicate if the string formatter is valid

    >>> check_format_str(".3E")
    >>> check_format_str(".3g")
    >>> check_format_str(".4f")
    >>> check_format_str("08,.1f")
    """

    text = text.strip()
    is_valid = True

    # basic length checks
    if len(text) < 2:
        is_valid = False
    elif 's' in text.lower():
        is_valid = False
    elif '%' not in text[0]:
        is_valid = False
    elif text[-1].lower() not in ['g', 'f', 'i', 'e']:
        is_valid = False

    # the float formatter handles ints/floats?
    text_no_percent = text[1:]
    try:
        format(1, text_no_percent)
        format(.2, text_no_percent)
        format(1e3, text_no_percent)
        format(-5., text_no_percent)
        format(-5, text_no_percent)
    except ValueError:
        is_valid = False
    except TypeError:
        is_valid = False

    if not is_valid:
        return text, is_valid

    # the float formatter isn't supposed to handle strings?
    # doesn't this break %g?
    try:
        text % 's'
        is_valid = False
    except (ValueError, TypeError):
        pass
    return text, is_valid


if __name__ == '__main__':  # pragma: no cover
    #assert check_format_str('%.3E')[1] is True
    #assert check_format_str('%.3g')[1] is True
    #assert check_format_str('%.4f')[1] is True
    #assert check_format_str('%08,.1f')[1] is True
    assert check_format_str('%08,.p1f')[1] is False
    assert _check_float('3.14') == 3.14
    assert _check_float('2,557') == 2.557

