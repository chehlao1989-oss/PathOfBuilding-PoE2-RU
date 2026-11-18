import argparse
import ctypes
import os
from pathlib import Path


def run_lua(directory, lua_path):
    runtime = directory / "lua51.dll"
    dll_handle = os.add_dll_directory(str(directory))
    os.chdir(directory)
    lua = ctypes.CDLL(str(runtime))
    lua.luaL_newstate.restype = ctypes.c_void_p
    lua.luaL_openlibs.argtypes = [ctypes.c_void_p]
    lua.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lua.lua_pcall.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lua.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    lua.lua_tolstring.restype = ctypes.c_char_p
    lua.lua_close.argtypes = [ctypes.c_void_p]
    state = lua.luaL_newstate()
    if not state:
        raise RuntimeError("Lua could not create a state")
    try:
        lua.luaL_openlibs(state)
        source = (
            'package.path = "./?.lua;./lua/?.lua;./lua/?/init.lua;" .. package.path\n'
            'package.cpath = "./?.dll;./?/core.dll;" .. package.cpath\n'
            + lua_path.read_text(encoding="utf-8")
        )
        status = lua.luaL_loadstring(state, source.encode("utf-8"))
        if status == 0:
            status = lua.lua_pcall(state, 0, 0, 0)
        if status:
            error = lua.lua_tolstring(state, -1, None)
            raise RuntimeError(error.decode("utf-8", "replace") if error else status)
    finally:
        lua.lua_close(state)
        dll_handle.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("script", type=Path)
    args = parser.parse_args()
    run_lua(args.directory.resolve(), args.script.resolve())
