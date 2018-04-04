from c_builder.c_file_writer import *

filename = r"c_test_autogen.c"
outputpath = r"sample_output"
indent = "    "


def create_files(outputpath, file_prefix, c_ext, h_ext, preamble_file, critical_enter, critical_exit, includes, get_thread, threads, structs, class_style):

    file_prefix += '_'
    filename = file_prefix + "shared_file" +  c_ext
    h_name = file_prefix + "shared_file" +  h_ext
    thread_name = file_prefix + "shared_file_threads" +  h_ext


    common_includes = ["<unistd.h>", "<stdbool.h>", "<stdint.h>"] \
                      + list(set(["\"" + s.header_which_defines_struct + "\"" for s in structs]))

    includes.extend(common_includes)
    class_name = file_prefix + "class"
    shared_type = file_prefix + "struct"
    shared_instance = "p_" + shared_type
    get_read = file_prefix + "{n}_read"
    get_write = file_prefix + "{n}_write"
    post_write =  file_prefix + "{n}_post"
    g = shared_instance

    with CFile(filename, outputpath, indent) as f:


        if preamble_file:
            with open(preamble_file, "w") as preamble:
                f.write(preamble.read())

        for i in includes + ["<string.h>", "\""+h_name+"\"", "\""+thread_name+"\""]:
            f.write("#include {}\n".format(i))

        f.write("\n")




        if class_style:
            with CCodeBlock("{class_name}::{class_name}(void * g_ptr, {file_prefix}threads_processes thread): \n".format(**locals())
                            + indent + "{shared_instance}(({shared_type} *) g_ptr),\n".format(**locals())
                            + indent + "m_thread(thread)", base=f) as constructor:
                pass
            class_prefix = "{class_name}::".format(**locals())
            get_thread = "m_thread"
        else:
            f.add_code_line("{}* {}".format(shared_type, shared_instance))
            class_prefix = ""



        with CCodeBlock("void {class_prefix}{file_prefix}init(void)".format(**locals()), base=f) as init:
            for s in structs:
                t = s.type
                n = s.name


                top_range = max(s.instance_count,1)
                init.add_code_line("{t}* p_{n}".format(**locals()))

                for i in range(0,top_range):
                    if s.instance_count:
                       inst = "{i}".format(**locals())
                    else:
                        inst = ""
                    init.add_code_line(("p_{n} = " + get_write +"({inst})" ).format(**locals()))
                    #init.add_code_line(("*p_{n} = {t}{{0}}").format(**locals()))  #todo might need
                    init.add_code_line("memset(p_{n},0,sizeof({t}))".format(**locals()))
                    init.add_code_line((post_write+ "({inst})").format(**locals()))

        for s in structs:
            t = s.type
            n = s.name
            if s.instance_count:
                inst_type = "uint8_t instance"
                inst = "[instance]"
            else:
                inst_type = "void"
                inst = ""


            with CCodeBlock(("{t}* {class_prefix}"+get_write+ "({inst_type})").format(**locals()), base=f) as write_func:
                if len(s.all_copies) == 1:
                    write_func.add_code_line("{g}->{n}_write{inst} = 0u".format(**locals()))
                else:
                    write_func.add_code_line(critical_enter)
                    for i in range(0, len(s.all_copies)):
                        if i < len(s.all_copies)-1:
                            if i == 0:
                                code_block = "if"
                            else:
                                code_block = "else if"

                            for j in range(0, len(s.read_copies)):
                                if j == 0:
                                    code_block += "("
                                else:
                                    code_block += " && "
                                copy = s.read_copies[j]
                                code_block += "({i}u != {g}->{n}_{copy}{inst})".format(**locals())
                            code_block+=")"
                        else:
                            code_block = "else"
                        with CCodeBlock(code_block, base=write_func) as write_if:
                            write_if.add_code_line("{g}->{n}_write{inst} = {i}u".format(**locals()))
                    write_func.add_code_line(critical_exit)
                    write_func.add_code_line(
                        "memcpy(&({g}->{n}_arr[{g}->{n}_write{inst}]{inst}), &({g}->{n}_arr[{g}->{n}_newest{inst}]{inst}), sizeof({t}))"
                            .format(**locals()))

                write_func.add_code_line("return &({g}->{n}_arr[{g}->{n}_write{inst}]{inst})".format(**locals()))

            with CCodeBlock(("void {class_prefix}"+post_write+ "({inst_type})").format(**locals()), base=f) as post_func:
                post_func.add_code_line(critical_enter)
                post_func.add_code_line("{g}->{n}_newest{inst}={g}->{n}_write{inst}".format(**locals()))
                post_func.add_code_line(critical_exit)

            with CCodeBlock(("{t}* {class_prefix}"+get_read+ "({inst_type})").format(**locals()), base=f) as read_func:
                read_func.add_code_line("{t}* rc".format(**locals()))
                read_func.add_code_line(critical_enter)

                with CCodeBlock("switch({})".format(get_thread),base = read_func) as switch:
                    for thread in [thr.name for thr in threads if thr.name in s.read_copies]:
                        with CCodeBlock("case {}{}:".format(file_prefix,thread), base = switch) as case:
                            case.add_code_line("{g}->{n}_{thread}{inst} = {g}->{n}_newest{inst}".format(**locals()))
                            case.add_code_line("rc = &({g}->{n}_arr[{g}->{n}_{thread}{inst}]{inst})".format(**locals()))
                            case.add_code_line("break")

                    with CCodeBlock("default:", base=switch) as case:
                            case.add_code_line("rc = &({g}->{n}_arr[{g}->{n}_newest{inst}]{inst})".format(**locals()))
                            case.add_code_line("break")

                read_func.add_code_line(critical_exit)
                read_func.add_code_line("return rc")

    filename = file_prefix + "shared_file" +  h_ext

    with CFile(h_name, outputpath, indent) as f:

        if preamble_file:
            with open(preamble_file, "w") as preamble:
                f.write(preamble.read())

        f.write("#ifndef __{0}__\n#define __{0}__\n".format(h_name.replace(".","_").upper()))


        for i in common_includes + ["\""+thread_name+"\""]:
            f.write("#include {}\n".format(i))

        f.write("\n")

        with CCodeBlock("typedef struct", base=f, block_segmenter=('{', '} '+shared_type + ";")) as c_struct:
            c_struct.add_code_line("uint8_t sem")
            c_struct.add_code_line("uint8_t sem2")

            for s in structs:
                if s.instance_count:
                    inst = "[{}u]".format(s.instance_count)
                else:
                    inst = ""

                t = s.type
                n = s.name
                for i in s.all_ptrs:
                    c_struct.add_code_line("uint8_t {n}_{i}{inst}".format(**locals()))
                s = len(s.all_copies)
                c_struct.add_code_line("{t} {n}_arr[{s}u]{inst}".format(**locals()))

        if class_style:
            f.write("class {class_name}".format(**locals()))
            f.write("{\n")
            f.write("public:\n")
            f.add_code_line("{class_name}(void * g_ptr, {file_prefix}threads_processes thread)".format(**locals()))



        f.add_code_line("void {}init(void)".format(file_prefix))

        for s in structs:
            if s.instance_count:
                inst_type = "uint8_t instance"
            else:
                inst_type = "void"
            t = s.type
            n = s.name
            f.add_code_line(("{t}* "+get_write+ "({inst_type})").format(**locals()))
            f.add_code_line(("void "+post_write+ "({inst_type})").format(**locals()))
            f.add_code_line(("{t}* "+get_read+ "({inst_type})").format(**locals()))

        if class_style:
            f.write("private:")
            f.add_code_line("{shared_type} * {shared_instance}".format(**locals()))
            f.add_code_line ("{file_prefix}threads_processes m_thread".format(**locals()))
            f.add_code_line("}\n")

        f.write("#endif\n")

    with CFile(thread_name, outputpath, indent) as f:
        if preamble_file:
            with open(preamble_file, "w") as preamble:
                f.write(preamble.read())

        f.write("#ifndef __{0}__\n#define __{0}__\n".format(thread_name.replace(".","_").upper()))

        with CCodeBlock("typedef enum", base=f, block_segmenter=('{', '} '+file_prefix + "threads_processes" + ";")) \
                as c_enum:
            c_enum.add_code_line("INVALID",termination=",")
            for i in range(0,len(threads)):
                c_enum.add_code_line(file_prefix+threads[i].name,termination = "," if i<len(threads)-1 else "")


        f.write("#endif\n")