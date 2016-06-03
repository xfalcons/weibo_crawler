# Weibo crawler

## INSTALL Python

需要 easy_install 各 pip , easy_install 和 pip 都是用来下载安装Python一个公共资源库相关资源包的

首先安装 easy_install

下载地址: https://pypi.python.org/pypi/ez_setup

解压,安装.

		python ez_setup.py

安装好 easy_install 之后 再安装 pip

下载地址: https://pypi.python.org/pypi/pip

解压,安装.

		python setup.py install

安装 Python 的虚拟环境（工作环境）

	    pip install virtualenv


## 创建环境

底下示范 weibo_crawler 环境


		[/home/kevin_luo]$ virtualenv weibo_crawler
		New python executable in weibo_crawler/bin/python
		Installing setuptools, pip...done.
		[/home/kevin_luo]$ 

很简单，就是virtualenv 环境名称[自定义的名称，自己喜欢什么就写什么]

默认情况下，虚拟环境会依赖系统环境中的site packages，就是说系统中已经安装好的第三方package也会安装在虚拟环境中，

如果不想依赖这些package，那么可以加上参数 --no-site-packages，建立虚拟环境

我们先进入到该目录下：

		[/home/kevin_luo]$ cd weibo_crawler/

然后启动

		[/home/kevin_luo/weibo_crawler]$ source ./bin/activate

启动成功后，会在前面多出 test_env 字样，如下所示

		(weibo_crawler)[/home/kevin_luo/weibo_crawler]$ 


## 安装应用环境

		(weibo_crawler)[/home/kevin_luo/weibo_crawler]$ pip install requests pycurl
		(weibo_crawler)[/home/kevin_luo/weibo_crawler]$ pip install selenium bs4 pyvirtualdisplay

You are good to go.

## 问题（坑）

### 编码问题

一般来说，只要在 python source code 里，添加

		reload(sys)
		sys.setdefaultencoding('utf-8')

但是，在我们的 CentOS 6.2 里，却不行，唉！谁叫你还用 6.2

does NOT take effect. And the weird environment on that CentOS is the LC_xx nor LANG setting.

It does NOT set default LC_ALL or LANG to UTF8.

So that when you run your python script, just remember to set user's LANG

		$ export LANG=en_US.UTF8 

搞定。

### chromedriver 在 CentOS 6.2 问题

CentOS 6.2 上的 libstdc++.so.6 没有包含 chromedriver 需要的 library

		13:18 [root@a01.spider.logstat.qingdao.youku]$ ./chromedriver
		./chromedriver: /usr/lib64/libstdc++.so.6: version `GLIBCXX_3.4.15' not found (required by ./chromedriver)
		./chromedriver: /usr/lib64/libstdc++.so.6: version `CXXABI_1.3.5' not found (required by ./chromedriver)

解法很麻烦，索性就使用 'webdrive.Firefox()', 运行比较慢

透过下列方式，虽然可以编译出 libstdc++.so.6 ，但是在执行 chromedriver 时，还是有问题，所以就先不解了。

You're missing the 32 bit libc dev package:

On Ubuntu it's called libc6-dev-i386 - do sudo apt-get install libc6-dev-i386. See below for extra instructions for Ubuntu 12.04.

On Red Hat distros, the package name is glibc-devel.i686 (Thanks to David Gardner's comment)

On CentOS 5.8, the package name is glibc-devel.i386 (Thanks to JimKleck's comment)

On CentOS 6 / 7, the package name is glibc-devel.i686.

I am using CentOs 6.4 x64bit

I downloaded "gcc-4.6.2.tar.gz" from "ftp://gd.tuwien.ac.at/gnu/gcc/releases/gcc-4.6.2"

[source of the below : "http://gcc.gnu.org/wiki/InstallingGCC":http://gcc.gnu.org/wiki/InstallingGCC]

		@tar xzf gcc-4.6.2.tar.gz
		cd gcc-4.6.2
		./contrib/download_prerequisites
		cd ..
		mkdir objdir
		cd objdir
		$PWD/../gcc-4.6.2/configure --prefix=/opt/gcc-4.6.2
		make
		make install@

After this is done, go to "/opt/gcc-4.6.2/lib64" you will be able to see "libstdc++.so.6" and "libstdc++.so.6.0.16".

Rename "/usr/lib64/libstdc++.so.6" to "/usr/lib64/llibstdc++.so.6.backup"

copy "/opt/gcc-4.6.2/lib64/libstdc++.so.6" and "/opt/gcc-4.6.2/lib64/libstdc++.so.6.0.16" to "usr/lib64/"

And now you can "./qt-linux-opensource-5.0.1-x86_64-offline.run"

You are free to go .... (i am currently using it)
