from c_builder.c_file_writer import *

filename = r"c_test_autogen.c"
outputpath = r"sample_output"
indent = "    "


def create_files(outputpath, file_prefix, c_ext, h_ext, preamble_file, critical_enter, critical_exit, includes, get_thread, threads, structs):

    filename = file_prefix + "_shared_file" +  c_ext
    h_name = file_prefix + "_shared_file" +  h_ext
    thread_name = file_prefix + "_shared_file_threads" +  h_ext


    includes.extend(["<unistd.h>", "<stdbool.h>", "<stdint.h>"])
    shared_type = file_prefix + "_struct"
    shared_instance = "p_" + shared_type
    get_read = file_prefix + "_{n}_read"
    get_write = file_prefix + "_{n}_write"
    post_write =  file_prefix + "_{n}_post"
    g = shared_instance

    with CFile(filename, outputpath, indent) as f:

        if preamble_file:
            with open(preamble_file, "w") as preamble:
                f.write(preamble.read())

        for i in includes + ["<string.h>", "\""+h_name+"\"", "\""+thread_name+"\""]:
            f.write("#include {}\n".format(i))

        for s in structs:
            f.write("#include \"{}\"\n".format(s.header_which_defines_struct))
        f.write("\n")


        f.add_code_line("{}* {}".format(shared_type, shared_instance))

        with CCodeBlock("void {}_init(void)".format(file_prefix), base=f) as init:
            for s in structs:
                t = s.type
                n = s.name
                init.add_code_line(("{t}* p_{n} = " + get_write +"()" ).format(**locals()))
                #init.add_code_line(("*p_{n} = {t}{{0}}").format(**locals()))  #todo might need
                init.add_code_line("memset(p_{n},0,sizeof({t}))".format(**locals()))

                init.add_code_line((post_write+ "()").format(**locals()))

        for s in structs:
            t = s.type
            n = s.name


            with CCodeBlock(("{t}* "+get_write+ "(void)").format(**locals()), base=f) as write_func:
                if len(s.all_copies) == 1:
                    write_func.add_code_line("{g}->{n}_write = 0u".format(**locals()))
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
                                code_block += "({i}u != {g}->{n}_{copy})".format(**locals())
                            code_block+=")"
                        else:
                            code_block = "else"
                        with CCodeBlock(code_block, base=write_func) as write_if:
                            write_if.add_code_line("{g}->{n}_write = {i}u".format(**locals()))
                    write_func.add_code_line(critical_exit)
                    write_func.add_code_line(
                        "memcpy(&({g}->{n}_arr[{g}->{n}_write]), &({g}->{n}_arr[{g}->{n}_newest]), sizeof({t}))"
                            .format(**locals()))

                write_func.add_code_line("return &({g}->{n}_arr[{g}->{n}_write])".format(**locals()))

            with CCodeBlock(("void "+post_write+ "(void)").format(**locals()), base=f) as post_func:
                post_func.add_code_line(critical_enter)
                post_func.add_code_line("{g}->{n}_newest={g}->{n}_write".format(**locals()))
                post_func.add_code_line(critical_exit)

            with CCodeBlock(("{t}* "+get_read+ "(void)").format(**locals()), base=f) as read_func:
                read_func.add_code_line("{t}* rc".format(**locals()))
                read_func.add_code_line(critical_enter)

                with CCodeBlock("switch({})".format(get_thread),base = read_func) as switch:
                    for thread in [thr.name for thr in threads if thr.name in s.read_copies]:
                        with CCodeBlock("case {}:".format(thread), base = switch) as case:
                            case.add_code_line("{g}->{n}_{thread} = {g}->{n}_newest".format(**locals()))
                            case.add_code_line("rc = &({g}->{n}_arr[{g}->{n}_{thread}])".format(**locals()))
                            case.add_code_line("break")

                    with CCodeBlock("default:", base=switch) as case:
                            case.add_code_line("rc = &({g}->{n}_arr[{g}->{n}_newest])".format(**locals()))
                            case.add_code_line("break")

                read_func.add_code_line(critical_exit)
                read_func.add_code_line("return rc")

    filename = file_prefix + "_shared_file" +  h_ext

    with CFile(h_name, outputpath, indent) as f:

        if preamble_file:
            with open(preamble_file, "w") as preamble:
                f.write(preamble.read())

        f.write("#ifndef __{0}__\n#define __{0}__\n".format(h_name.replace(".","_").upper()))


        for i in includes + ["\""+thread_name+"\""]:
            f.write("#include {}\n".format(i))
        for s in structs:
            f.write("#include \"{}\"\n".format(s.header_which_defines_struct))

        f.write("\n")

        with CCodeBlock("typedef struct", base=f, block_segmenter=('{', '} '+shared_type + ";")) as c_struct:
            c_struct.add_code_line("uint8_t sem")
            c_struct.add_code_line("uint8_t sem2")

            for s in structs:
                t = s.type
                n = s.name
                for i in s.all_ptrs:
                    c_struct.add_code_line("uint8_t {n}_{i}".format(**locals()))
                s = len(s.all_copies)
                c_struct.add_code_line("{t} {n}_arr[{s}u]".format(**locals()))



        f.add_code_line("void {}_init(void)".format(file_prefix))

        for s in structs:
            t = s.type
            n = s.name
            f.add_code_line(("{t}* "+get_write+ "(void)").format(**locals()))
            f.add_code_line(("void "+post_write+ "(void)").format(**locals()))
            f.add_code_line(("{t}* "+get_read+ "(void)").format(**locals()))

        f.write("#endif\n")

    with CFile(thread_name, outputpath, indent) as f:
        if preamble_file:
            with open(preamble_file, "w") as preamble:
                f.write(preamble.read())

        f.write("#ifndef __{0}__\n#define __{0}__\n".format(thread_name.replace(".","_").upper()))

        for i in includes:
            f.write("#include {}\n".format(i))

        with CCodeBlock("typedef enum", base=f, block_segmenter=('{', '} '+file_prefix + "_threads_processes" + ";")) \
                as c_enum:

            for i in range(0,len(threads)):
                c_enum.add_code_line(threads[i].name,termination = "," if i<len(threads)-1 else "")


        f.write("#endif\n")