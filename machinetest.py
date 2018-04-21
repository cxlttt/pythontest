# coding:utf-8

from __future__ import division
import sys, time, datetime, telnetlib, ConfigParser, fileinput, os, re, exceptions, hashlib
import ctypes
import re

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE= -11
STD_ERROR_HANDLE = -12

FOREGROUND_BLACK = 0x0
FOREGROUND_BLUE = 0x01 # text color contains blue.
FOREGROUND_GREEN= 0x02 # text color contains green.
FOREGROUND_RED = 0x04 # text color contains red.
FOREGROUND_INTENSITY = 0x08 # text color is intensified.

BACKGROUND_BLUE = 0x10 # background color contains blue.
BACKGROUND_GREEN= 0x20 # background color contains green.
BACKGROUND_RED = 0x40 # background color contains red.
BACKGROUND_INTENSITY = 0x80 # background color is intensified.


#Color class, to print colored chars
class Color:
    ''''' See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winprog/winprog/windows_api_reference.asp
    for information on Windows APIs.'''
    std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    def set_cmd_color(self, color, handle=std_out_handle):
        """(color) -> bit
        Example: set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY)
        """
        bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
        return bool

    def reset_color(self):
        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)

    def print_red_text(self, print_text):
        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        print print_text.decode('utf-8')
        self.reset_color()

    def print_green_text(self, print_text):
        self.set_cmd_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
        print print_text.decode('utf-8')
        self.reset_color()

    def print_blue_text(self, print_text):
        self.set_cmd_color(FOREGROUND_BLUE | FOREGROUND_INTENSITY)
        print print_text.decode('utf-8')
        self.reset_color()

    def print_red_text_with_blue_bg(self, print_text):
        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY| BACKGROUND_BLUE | BACKGROUND_INTENSITY)
        print print_text.decode('utf-8')
        self.reset_color()

g_clr = Color()

# 根据文件名，计算md5
def md5sum(filename):
    fd = open(filename, "r")
    fcont = fd.read()
    fd.close()
    fmd5 = hashlib.md5(fcont)
    return fmd5


#
# 程序读取配置文件，返回所有配置文件字段。
#
def readConfig(name):
    config = ConfigParser.ConfigParser()

    try:
        with open(name, 'r') as cfgFile:
            config.readfp(cfgFile)
            return config
    except IOError, e:
        print '程序没有找到配置文件，程序当前目录需要config.ini文件。'.decode('utf-8')

        sys.exit()


#
# 检查配置文件是否正确
#
def checkConfig(config):
    config = readConfig(config);
    items = config.options('items')
    for item in items:
        if not config.has_option('target', item):
            print '配置文件参数数量不匹配'.decode('utf-8')
            sys.exit()

    return config


# 准备网络
#
# 登陆Telnet，自动输入用户名密码，完成后打印成功
#
def ReadyNet(host, user, passwd):
    try:
        telnetfp = telnetlib.Telnet(host, timeout=3)

        telnetfp.read_until("ogin: ")
        telnetfp.write(user + "\r\n")
        telnetfp.read_until("assword: ")
        telnetfp.write(passwd + "\r\n")
        return telnetfp

    except IOError, e:
        raise e


#
# 获取用户输入产品号，附带输入信息；
#
def getInputGiveInfo():
    try:
        print "<按［回车］键，开始检查>".decode('utf-8')
        return str(input('>>>'))
    except IOError, e:
        print '请输入正确格式的信息。'.decode('utf-8')
    except SyntaxError, e:
        return ''


#
# 检查所选项目是否正确
#
def CheckMsg(msg, target):
    return msg.find(target)


#
# 处理网络连接，逐项检查常规检查
#
def checkDevice(config):
    items = config.options('items')

    for item in items:
        lNet = ReadyNet(config.get('info', 'host'), config.get('info', 'user'), config.get('info', 'passwd'))
        lNet.write(config.get('items', item) + "\r\n")
        lNet.write("exit" + "\r\n")
        msg = lNet.read_all()
        if CheckMsg(msg, config.get('target', item)) == -1:
            print str(config.get('name', item) + "\t错误\t" + config.get('target', item)).decode('utf-8')
        else:
            print str(config.get('name', item) + "\t正确\t" + config.get('target', item)).decode('utf-8')
        lNet.close()
        time.sleep(0.2)
    print "\n\n"


#
# 检查设备时间误差
#
def checkDateTime(config):
    lNet = ReadyNet(config.get('info', 'host'), config.get('info', 'user'), config.get('info', 'passwd'))
    lNet.write("date +\"UTC:%Y-%m-%d %T\"" + "\r\n")
    lNet.write("exit" + "\r\n")
    msg = lNet.read_all()

    ok = 1

    pos = msg.rfind("UTC")
    deviceDate = datetime.datetime.strptime(msg[pos + 4:pos + 23], "%Y-%m-%d %H:%M:%S")
    devation = deviceDate - datetime.datetime.now()
    cas = (devation.days * 24 * 3600 + devation.seconds)
    if abs(cas) > 5:
        #print "对时\t错误\t时间差距%d秒".decode('utf-8') % cas
        g_clr.print_red_text("对时\t错误\t时间差距%d秒" % cas)
        ok = 0
    else:
        print "对时\t正确\t时间差距%d秒".decode('utf-8') % cas

    lNet.close()
    return ok


#
# 检查设备固件版本
#
def checkSoftVersion(config):
    lNet = ReadyNet(config.get('info', 'host'), config.get('info', 'user'), config.get('info', 'passwd'))
    lNet.write("cd /nand/bin/ ;md5sum *" + "\r\n")
    lNet.write("cd /nor/lib/ ;md5sum *" + "\r\n")
    lNet.write("cd /nor/config/ ;md5sum *" + "\r\n")
    lNet.write("cd /nor/ppp/ ;md5sum cdma2000-connect-chat" + "\r\n")
    lNet.write("cd /nor/ppp/peers/ ;md5sum cdma2000" + "\r\n")
    lNet.write("exit" + "\r\n")
    msg = lNet.read_all()

    ok = 1

    f = open('md5.ini', 'r')

    for i in f:
        if msg.find(i[:24]) == -1:
            g_clr.print_red_text("版本\t错误\t" + i.split('  ')[1])
            ok = 0
    f.close()

    if ok == 0:
        g_clr.print_red_text("程序版本检查 <<<<<<<<错误>>>>>>>>\n\n")
    else:
        print "程序版本检查-正确！\n\n".decode('utf-8')

    lNet.close()
    return ok


#
# 检查电池电压
#


#
# 检查电池电压
#
def checkNormal(config):
    lNet = ReadyNet(config.get('info', 'host'), config.get('info', 'user'), config.get('info', 'passwd'))
    lNet.write("cat /nand/check.log" + "\r\n")
    lNet.write("cat /proc/version" + "\r\n")
    lNet.write("cj bt 3.5" + "\r\n")
    lNet.write("exit" + "\r\n")
    msg = lNet.read_all()

    ok = 1

    print "USB\t正确".decode('utf-8')

    if msg.find("485OK") > 0:
        print "485\t正确".decode('utf-8')
    else:
        g_clr.print_red_text("485\t错误")
        ok = 0

    if msg.find("主站证书 OK") > 0:
        print "ESAM\t正确".decode('utf-8')
    else:
        g_clr.print_red_text("ESAM\t错误")
        ok = 0

    if msg.find(config.get('target', 'kernal')) > 0:
        print "内核\t正确".decode('utf-8')
    else:
        g_clr.print_red_text("内核\t错误")
        ok = 0

    lNet = ReadyNet(config.get('info', 'host'), config.get('info', 'user'), config.get('info', 'passwd'))
    lNet.write("cj bt 3.5" + "\r\n")
    lNet.write("exit" + "\r\n")
    msg = lNet.read_all()

    #print msg
    #print re.findall(r'\-*\d+(?:\.\d+)?', msg)
    battery = re.findall(r'\-*\d+(?:\.\d+)?', msg.split("\r\n")[-3])[0]
    #print battery
    flt = float(battery)

    config = readConfig("./check.ini");
    item = config.get("items", "battery")
    target = re.findall(r'\-*\d+(?:\.\d+)?', item)[0]
    #print "target battery: %s"%target

    if flt > float(target):
        print "电池\t正确".decode('utf-8')
    else:
        g_clr.print_red_text("电池\t错误")
        ok = 0

    lNet.close()
    return ok


#
# 输出设备ID
#
def showDeviceId(config):
    lNet = ReadyNet(config.get('info', 'host'), config.get('info', 'user'), config.get('info', 'passwd'))
    lNet.write("cj ip 119.180.24.156:6360 119.180.24.156:6360" + "\r\n")
    lNet.write("cj apn cmnet" + "\r\n")
    lNet.write("cj id 00 00 00 00 00 01" + "\r\n")
    lNet.write("cj heart 60" + "\r\n")
    lNet.write("cj checkled &" + "\r\n")
    lNet.write("cd /nor/ppp/ ;md5sum cdma2000-connect-chat" + "\r\n")
    lNet.write("cd /nor/ppp/peers/ ;md5sum cdma2000" + "\r\n")
    lNet.write("exit" + "\r\n")
    msg = lNet.read_all()

    lNet.close()
    return 1


if __name__ == '__main__':
    config = checkConfig("./check.ini")
    while True:
        try:
            getInputGiveInfo()

            ok = 1

            os.system('cls;clear')
            os.system('arp -d')
            ok &= checkNormal(config);
            ok &= checkSoftVersion(config)
            ok &= checkDateTime(config)
            ok &= showDeviceId(config)

            if ok == 1:
                print "\n\n\n>>>>>>>>>>>>>>>>>全部正确\n\n\n".decode('utf-8')
            else:
                g_clr.print_red_text("\n\n\n>>>>>>>>>>>>>>>>>设备异常!!!!!\n\n\n")
        except IOError, e:
            print '网络连接错误，检查网线连接状态。'.decode('utf-8')
            continue
