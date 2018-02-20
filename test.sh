p=$(pidof a.out)
kill $p
sudo pip install -r requirements.txt
python share_files.py test.yaml
cd c_files
cd test
rm -f *.out
gcc ../output/shs_shared_file.c main.c ../lib/linux_ipc.c -I. -I./../lib -I./../output
echo "test may take up to a minute"
./a.out 1 &
./a.out 2 &
./a.out 3
p=$(pidof a.out)
kill $p