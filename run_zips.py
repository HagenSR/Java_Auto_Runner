import os
import glob
import zipfile
import shutil
import os.path
import subprocess
from subprocess import STDOUT, PIPE
from multiprocessing import Process


class ZipRunner:

    def __init__(self, zip_dir=".\\zips", build_dir=".\\build", output_dir=".\\out", max_time=100) -> None:
        self.zip_dir = zip_dir
        self.build_dir = build_dir
        self.create_or_remove(self.build_dir)
        self.output_dir = output_dir
        self.create_or_remove(self.output_dir)
        self.MAX_TIMEOUT = max_time

    def create_or_remove(self, folder: str):
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.mkdir(folder)

    def run(self):
        self.unzip()
        self.build()

    def unzip(self):
        zips = glob.glob(f"{self.zip_dir}/*.zip")
        for zip in zips:
            try:
                with zipfile.ZipFile(zip, "r") as zip_ref:
                    file_name = zip.split("\\")[-1].lower().replace(".zip", "")
                    zip_ref.extractall(f"{self.build_dir}/{file_name}")
            except Exception as e:
                print(f"Failed to extract {zip}")

    def build(self):
        dirs = os.listdir(self.build_dir)
        for dir in dirs:
            print(f"Starting {dir}")
            file_name = dir.split("\\")[-1].lower()
            try:
                proc = Process(
                    target=self.build_internal, args=[dir]
                )
                proc.start()
                proc.join(self.MAX_TIMEOUT)
                if proc.is_alive():
                    raise TimeoutError()
            except TimeoutError:
                proc.kill()
                print(f"{file_name}: Did not complete in time")
                self.write_to_file(file_name, "failed to finish task in time")

    def build_internal(self, dir: str):
        try:
            src_dir, client_file, package = self.get_build_info(dir)
            self.compile_java(dir, src_dir, client_file)
            self.execute_java(dir, src_dir, package)
        except Exception as e:
            print(f"{dir}: {str(e)}")
            self.write_to_file(dir, str(e))

    def compile_java(self, dir: str, src_dir: str, java_file: str):
        cmd = " ".join(['javac', '-d', f'build/{dir}/out/',
                        '-classpath', f'{src_dir}/.', f'{java_file}'])
        proc = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        stdout, stderr = proc.communicate()
        combined = [line for line in stdout.decode(
            "utf-8").split("\n") if "Note:" not in line]
        combined = "\n".join(combined)
        if combined or stderr:
            self.write_to_file(dir, combined if combined else stderr)
            raise Exception("Failed to compile")

    def execute_java(self, fileName: str, src_dir: str, package: str):
        cmd = " ".join(
            ['java', '-cp', f'..\\out\\.', f'{package}'])
        st = open("input.in")
        proc = subprocess.Popen(
            cmd, stdin=st, stdout=PIPE, stderr=STDOUT, shell=False, cwd=f'{src_dir}\\..')
        stdout, stderr = proc.communicate()
        self.write_to_file(fileName, stdout if stdout is not None else stderr)

    def write_to_file(self, filename: str, res):
        if type(res) is str:
            res = bytes(res, "utf-8")
        with open(f".\\{self.output_dir}\\{filename}.txt", "ab+") as fl:
            fl.write(res)

    def get_build_info(self, dir: str):
        parts = []
        file, contents = self.find_client_file(dir)
        jv_class = "Client"
        for part in file.split("\\"):
            parts.append(part)
            if part == "src":
                break
        package = ""
        for line in contents.split("\n"):
            if "public class " in line:
                jv_class = line.strip().removeprefix(
                    "public class").removesuffix("{").strip()
            if "package" in line:
                package = line.strip().removeprefix(
                    "package").removesuffix(";").strip()
        if package == "":
            return "\\".join(parts), file, jv_class
        else:
            return "\\".join(parts), file, package + f".{jv_class}"

    def find_client_file(self, dir: str):
        files = [os.path.join(dp, f) for dp, dn, fn in os.walk(
            os.path.expanduser(f"./build/{dir}")) for f in fn]
        for file in files:
            if not file.lower().endswith(".java"):
                continue
            contents = ""
            with open(file) as fl:
                contents = fl.read()
            if "public static void main" in contents:
                return file, contents
        raise Exception("Main method not found")


if __name__ == "__main__":
    run = ZipRunner(max_time=100)
    run.run()
