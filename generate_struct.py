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
    get_read = file_prefix + "_{t}_read"
    get_write = file_prefix + "_{t}_write"
    post_write =  file_prefix + "_{t}_post"


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
                init.add_code_line(("{t}* p_{t} = " + get_write +"()" ).format(t=s.name))
                init.add_code_line(("*p_{t} = ({t}){{0}}").format(t=s.name))
                init.add_code_line((post_write+ "()").format(t=s.name))

        for s in structs:
            with CCodeBlock(("{t}* "+get_write+ "(void)").format(t=s.name), base=f) as write_func:
                if len(s.all_copies) == 1:
                    write_func.add_code_line("{g}->{t}_write = 0u".format(g=shared_instance,t=s.name))
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
                                code_block += "({}u != {}->{}_{})".format(i,shared_instance,s.name,s.read_copies[j])
                            code_block+=")"
                        else:
                            code_block = "else"
                        with CCodeBlock(code_block, base=write_func) as write_if:
                            write_if.add_code_line("{}->{}_write = {}u".format(shared_instance,s.name,i))
                    write_func.add_code_line(critical_exit)
                    write_func.add_code_line(
                        "memcpy(&({g}->{t}_arr[{g}->{t}_write]), &({g}->{t}_arr[{g}->{t}_newest]), sizeof({t}))"
                            .format(g=shared_instance, t=s.name))

                write_func.add_code_line("return &({g}->{t}_arr[{g}->{t}_write])".format(g=shared_instance,t = s.name))

            with CCodeBlock(("void "+post_write+ "(void)").format(t=s.name), base=f) as post_func:
                post_func.add_code_line(critical_enter)
                post_func.add_code_line("{g}->{t}_newest={g}->{t}_write".format(g = shared_instance, t= s.name))
                post_func.add_code_line(critical_exit)

            with CCodeBlock(("{t}* "+get_read+ "(void)").format(t=s.name), base=f) as read_func:
                read_func.add_code_line("{t}* rc".format(t=s.name))
                read_func.add_code_line(critical_enter)

                with CCodeBlock("switch({})".format(get_thread),base = read_func) as switch:
                    for thread in [thr.name for thr in threads if thr.name in s.read_copies]:
                        with CCodeBlock("case {}:".format(thread), base = switch) as case:
                            case.add_code_line("{g}->{t}_{thr} = {g}->{t}_newest".format(g=shared_instance,t=s.name,
                                                                                            thr=thread))
                            case.add_code_line("rc = &({g}->{t}_arr[{g}->{t}_{thr}])"
                                               .format(g=shared_instance,t=s.name,thr=thread))
                            case.add_code_line("break")

                    with CCodeBlock("default:".format(thread), base=switch) as case:
                            case.add_code_line("rc = &({g}->{t}_arr[{g}->{t}_{thr}])"
                                               .format(g=shared_instance,t=s.name,thr="newest"))
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
            for s in structs:
                for i in s.all_ptrs:
                    c_struct.add_code_line("uint8_t {t}_{p}".format(t=s.name,p=i))
                c_struct.add_code_line("{t} {t}_arr[{s}u]".format(t=s.name, s=len(s.all_copies)))



        f.add_code_line("void {}_init(void)".format(file_prefix))

        for s in structs:
            f.add_code_line(("{t}* "+get_write+ "(void)").format(t=s.name))
            f.add_code_line(("void "+post_write+ "(void)").format(t=s.name))
            f.add_code_line(("{t}* "+get_read+ "(void)").format(t=s.name))

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