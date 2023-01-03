"""
Run python sandboxed.

This file is part of the source code for the Python Guilded's bot.
Copyright (C) 2023  Koviubi56

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

-----------------------------------------------------------------------------

Some parts of this code were copied from github zopefoundation/AccessControl
in 2023:

Copyright (c) 2002 Zope Foundation and Contributors.

Zope Public License (ZPL) Version 2.1

A copyright notice accompanies this license document that identifies the
copyright holders.

This license has been certified as open source. It has also been designated as
GPL compatible by the Free Software Foundation (FSF).

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions in source code must retain the accompanying copyright
notice, this list of conditions, and the following disclaimer.

2. Redistributions in binary form must reproduce the accompanying copyright
notice, this list of conditions, and the following disclaimer in the
documentation and/or other materials provided with the distribution.

3. Names of the copyright holders must not be used to endorse or promote
products derived from this software without prior written permission from the
copyright holders.

4. The right to distribute this software or to use it for any purpose does not
give you the right to use Servicemarks (sm) or Trademarks (tm) of the
copyright
holders. Use of them is covered by separate agreement with the copyright
holders.

5. If any files are modified, you must cause the modified files to carry
prominent notices stating that you changed the files and the date of any
change.

Disclaimer

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESSED
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL THE COPYRIGHT HOLDERS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
# SPDX-License-Identifier: GPL-3.0-or-later
# pylint: disable=protected-access
import threading
import traceback
import types
from typing import cast

import mylog
import RestrictedPython
from RestrictedPython import Eval, Guards

logger = mylog.root.get_child()
logger.threshold = mylog.Level.debug

NOT_ALLOWED = [
    "open(",
    "subprocess",
    "os",
    "sys",
    "shutil",
    "winreg",
    "tb_frame",
    "f_back",
    "f_globals",
    "sleep",
]


class ThreadWithReturnValue(threading.Thread):
    def __init__(self, *_args, **_kwargs):
        threading.Thread.__init__(self, *_args, **_kwargs)
        self._return = None
        self._exception = None

    def run(self):
        if self._target is not None:
            try:
                self._return = self._target(*self._args, **self._kwargs)
            except BaseException as exc:
                self._exception = exc

    def join(self, *args):
        threading.Thread.join(self, *args)
        return self._return


def check_not_allowed(source_code: str) -> bool:
    return any(not_allowed in source_code for not_allowed in NOT_ALLOWED)


def safer_import(name: str, *args, **kwargs) -> types.ModuleType:
    if name in NOT_ALLOWED:
        raise ImportError(f"cannot import {name}")
    # the following is probably unnecessary, but just to be sure...
    for not_allowed in NOT_ALLOWED:
        if not_allowed in name:
            raise ImportError(f"cannot import {name}")

    return __import__(name, *args, **kwargs)


def restricted_compile(source_code: str) -> types.CodeType:
    logger.info("Compiling code...")
    _compile_result = RestrictedPython.compile_restricted_exec(
        source_code,
        filename="<inline code>",
    )

    if _compile_result.errors:
        logger.warning(f"Compiled {source_code!r} with errors!")
        error = "\n".join(_compile_result.errors)
        raise RuntimeError(
            "Could not compile your code:"
            f"\n```text\n{error}```\nNOTE: For"
            " security reasons, some python functionalities are not allowed."
            " If you think that this error is not your fault but ours, contact"
            " staff, please."
        )
    logger.info("Compiled successfully!")

    return _compile_result.code


# vvvvv THIS PART OF THE CODE WAS COPIED. SEE MODULE DOCSTRING FOR MORE INFO

valid_inplace_types = (list, set)


inplace_slots = {
    "+=": "__iadd__",
    "-=": "__isub__",
    "*=": "__imul__",
    "/=": (1 / 2 == 0) and "__idiv__" or "__itruediv__",
    "//=": "__ifloordiv__",
    "%=": "__imod__",
    "**=": "__ipow__",
    "<<=": "__ilshift__",
    ">>=": "__irshift__",
    "&=": "__iand__",
    "^=": "__ixor__",
    "|=": "__ior__",
}


def __iadd__(x, y):
    x += y
    return x


def __isub__(x, y):
    x -= y
    return x


def __imul__(x, y):
    x *= y
    return x


def __idiv__(x, y):
    x /= y
    return x


def __ifloordiv__(x, y):
    x //= y
    return x


def __imod__(x, y):
    x %= y
    return x


def __ipow__(x, y):
    x **= y
    return x


def __ilshift__(x, y):
    x <<= y
    return x


def __irshift__(x, y):
    x >>= y
    return x


def __iand__(x, y):
    x &= y
    return x


def __ixor__(x, y):
    x ^= y
    return x


def __ior__(x, y):
    x |= y
    return x


inplace_ops = {
    "+=": __iadd__,
    "-=": __isub__,
    "*=": __imul__,
    "/=": __idiv__,
    "//=": __ifloordiv__,
    "%=": __imod__,
    "**=": __ipow__,
    "<<=": __ilshift__,
    ">>=": __irshift__,
    "&=": __iand__,
    "^=": __ixor__,
    "|=": __ior__,
}


def protected_inplacevar(op, var, expr):
    """Do an inplace operation
    If the var has an inplace slot, then disallow the operation
    unless the var an instance of ``valid_inplace_types``.
    """
    if hasattr(var, inplace_slots[op]) and not isinstance(
        var, valid_inplace_types
    ):
        try:
            cls = var.__class__
        except AttributeError:
            cls = type(var)
        raise TypeError(
            "Augmented assignment to %s objects is not allowed"
            " in untrusted code" % cls.__name__
        )
    return inplace_ops[op](var, expr)


# ^^^^^ THIS PART OF THE CODE WAS COPIED. SEE MODULE DOCSTRING FOR MORE INFO


def get_vars() -> dict[str, object]:
    logger.info("Making variables...")
    vars_ = RestrictedPython.safe_builtins
    vars_.update(RestrictedPython.limited_builtins)
    vars_.update(RestrictedPython.utility_builtins)
    vars_["_print_"] = RestrictedPython.PrintCollector
    vars_["_write_"] = Guards.full_write_guard
    vars_["__metaclass__"] = type
    vars_["__name__ "] = "__main__"
    vars_["_getiter_"] = Eval.default_guarded_getiter
    vars_["_iter_unpack_sequence_"] = Guards.guarded_iter_unpack_sequence
    vars_["getattr"] = Guards.safer_getattr
    vars_["_getattr_"] = Guards.safer_getattr
    vars_["_getitem_"] = Eval.default_guarded_getitem
    vars_["_inplacevar_"] = protected_inplacevar
    vars_["__import__"] = safer_import
    return vars_


def restricted_execute(
    _byte_code: types.CodeType,
    _globals: dict[str, object],
    _locals: dict[str, object],
    _source_code: str,
) -> dict[str, object]:
    try:
        logger.info(f"Executing the code... ({_byte_code = !r}s)")
        exec(  # pylint: disable=exec-used  # noqa: S102
            _byte_code,
            _globals,
            _locals,
        )
    except Exception as exc:
        logger.warning(
            f"Exception while executing code {_source_code!r}: {exc}"
        )
        raise RuntimeError(
            f"Could not run your code:\n```py\n{traceback.format_exc()}```"
            "\nNOTE: For security reasons, some python functionalities are not"
            " allowed. If you think that this error is not your fault but"
            " ours, contact staff, please."
        ) from exc
    logger.info("Executed successfully! ✨ 🍰 ✨ ")
    return _locals


def restricted_run(_source_code: str) -> str:
    _source_code += "\n\nresult = printed"
    logger.debug(f"New code: {_source_code!r}")
    _byte_code = restricted_compile(_source_code)

    _vars = get_vars()
    _globals: dict[str, object] = {"__builtins__": _vars}
    _locals: dict[str, object] = {"__builtins__": _vars}
    logger.debug("Set _globals and _locals to _vars")

    _locals = restricted_execute(_byte_code, _globals, _locals, _source_code)

    try:
        logger.debug("Returning `result`...")
        rv = _locals["result"]
        return cast(str, rv)
    except KeyError as exc:
        logger.critical('Could not return _locals["result"] !!!', True)
        raise RuntimeError(
            "Could not get the output of your code. Please contact staff."
        ) from exc


def main(source_code: str) -> str:
    logger.info(f"Executing code: {source_code!r}...")
    with logger.ctxmgr:
        logger.info("Checking if it has anything that is not allowed...")
        with logger.ctxmgr:
            if check_not_allowed(source_code):
                logger.error(f"Code {source_code!r} has NOT ALLOWED stuff!")
                raise RuntimeError(
                    """Your code is not allowed to be ran for security\
 reasons. The usage of
- the `subprocess`, `os`, `sys`, `shutil`, and `winreg` modules; and
- `open()`, and `time.sleep()`
is not allowed."""
                )
            logger.info("Nope, it's safe")

        logger.info("Creating thread...")
        thread = ThreadWithReturnValue(
            target=restricted_run,
            name=f"Thread-execute-{hash(source_code)}",
            args=(source_code,),
        )
        logger.info("Starting and joining thread...")
        thread.start()
        return_value = thread.join(5)
        if thread._exception:
            logger.info("Join returned, but there's an exception! Reraise it")
            raise thread._exception
        if thread.is_alive():
            logger.error("Join returned, thread is still alive; TIMED OUT!")
            raise RuntimeError(
                "Execution timed out. Please don't do that again! The {} team"
                " has been notified"
            )
        logger.info(f"Join returned, returning {return_value[:255]}")
        return return_value
