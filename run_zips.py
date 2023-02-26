import os
import glob
import zipfile
import shutil
import os.path
import subprocess
from subprocess import STDOUT, PIPE
from multiprocessing import Process


class zipRunner:

    def __init__(self, zipDir=".\\zips", buildDir=".\\build", outputDir=".\\out", stdIn=None, maxTime=200) -> None:
        self.zipDir = zipDir
        self.buildDir = buildDir
        self.createOrRemove(self.buildDir)
        self.outputDir = outputDir
        self.createOrRemove(self.outputDir)
        self.stdIn = stdIn
        self.MAX_TIMEOUT = maxTime

    def createOrRemove(self, folder):
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.mkdir(folder)

    def run(self):
        self.unzip()
        self.build()

    def unzip(self):
        zips = glob.glob(f"{self.zipDir}/*.zip")
        for zip in zips:
            with zipfile.ZipFile(zip, "r") as zipref:
                fileName = zip.split("\\")[-1].lower().replace(".zip", "")
                zipref.extractall(f"{self.buildDir}/{fileName}")

    def build(self):
        dirs = os.listdir(self.buildDir)
        for dir in dirs:
            print(f"Starting {dir}")
            fileName = dir.split("\\")[-1].lower()
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
                print(f"{fileName}: Did not complete in time")
                self.write_to_file(fileName, "failed to finish task in time")

    def build_internal(self, dir):
        try:
            src_dir, client_file, package = self.get_build_info(dir)
            self.compile_java(dir, src_dir, client_file)
            self.execute_java(dir, package)
        except Exception as e:
            print(f"{dir}: {str(e)}")

    def compile_java(self, dir, src_dir, java_file):
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

    def execute_java(self, fileName, package):
        cmd = " ".join(
            ['java', '-cp', f'.\\build\\{fileName}\\out\\.', f'{package}'])
        proc = subprocess.Popen(
            cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=False)
        stdout, stderr = proc.communicate(self.stdIn)
        self.write_to_file(fileName, stdout if stdout is not None else stderr)

    def write_to_file(self, filename, res):
        if type(res) is str:
            res = bytes(res, "utf-8")
        with open(f".\\{self.outputDir}\\{filename}.txt", "wb+") as fl:
            fl.write(res)

    def get_build_info(self, dir):
        parts = []
        file, contents = self.findClientFile(dir)
        jv_class = "Client"
        for part in file.split("\\"):
            parts.append(part)
            if part == "src":
                break
        package = "Client"
        for line in contents.split("\n"):
            if "public class " in line:
                jv_class = line.removeprefix(
                    "public class").removesuffix("{").strip()
            if "package" in line:
                package = line.removeprefix(
                    "package").removesuffix(";").strip()
        return "\\".join(parts), file, package + f".{jv_class}"

    def findClientFile(self, dir):
        files = [os.path.join(dp, f) for dp, dn, fn in os.walk(
            os.path.expanduser(f"./build/{dir}")) for f in fn]
        for file in files:
            contents = ""
            with open(file) as fl:
                contents = fl.read()
            if "public static void main" in contents:
                return file, contents
        raise Exception("Main method not found")


if __name__ == "__main__":
    run = zipRunner(stdIn=b"100")
    run.run()
