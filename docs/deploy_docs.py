import subprocess as sp

def run(cmd):
    print sp.check_output(cmd, shell=True)


run('git diff --exit-code')

run('make html')
#run('cp -R _build/html /tmp/gk_docs')
#run('cp -R ../.gitignore ~/tmp')

run('git checkout gh-pages')
run('git rm -rf .')
run('cp -R _build/html/* ../')
run('touch .nojekyll')
run('git add . -A; git commit -am "gh-pages"')
run('git push')
run('git checkout master')
