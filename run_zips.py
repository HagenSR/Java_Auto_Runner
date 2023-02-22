import os
import glob
import zipfile  
import shutil
import os.path,subprocess
from subprocess import STDOUT,PIPE
from multiprocessing import Process



class zipRunner:

    def __init__(self, zipDir = ".\\zips", buildDir = ".\\build", outputDir = ".\\out", stdIn = None, maxTime = 200) -> None:
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
                    target=self.build_internal, args = [dir]
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
            fileName = dir.split("\\")[-1].lower()
            client = "\\".join(self.returnClientFile(dir).split("\\")[0:-1])
            self.compile_java(dir, client, fileName)
            self.execute_java(fileName)
        except Exception as e:
            print(f"{fileName}: {str(e)}")

    def compile_java(self, dir, java_file, fileName):
        cmd = ['javac', '-d', f'build/{dir}/out/', '-classpath', f'{java_file}/.', f'{java_file}/Client.java']
        proc = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        stdout,stderr = proc.communicate()
        combined = [line for line in stdout.decode("utf-8").split("\n") if "Note:" not in line]
        combined = "\n".join(combined)
        if combined or stderr:
            self.write_to_file(fileName, combined if combined else stderr)
            raise Exception("Failed to compile")

    def execute_java(self, fileName):
        cmd = ['java', '-cp', f'.\\build\\{fileName}\\out\\', 'Client']
        proc = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        stdout,stderr = proc.communicate(self.stdIn)
        self.write_to_file(fileName, stdout if stdout is not None else stderr)

    def write_to_file(self, filename, res):
        if type(res) is str:
            res = bytes(res, "utf-8")
        with open(f".\\{self.outputDir}\\{filename}.txt", "wb+") as fl:
            fl.write(res)
        

    def returnClientFile(self, dir):
        return glob.glob(f"{self.buildDir}\\{dir}\\**\\Client.java", recursive=True)[0]

if __name__ == "__main__":
    run = zipRunner(stdIn=b"100")
    run.run()

