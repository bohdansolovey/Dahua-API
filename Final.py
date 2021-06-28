import requests
from requests.auth import HTTPDigestAuth
from requests.auth import HTTPBasicAuth
from time import gmtime, strftime
import ipaddress
from colorama import init
from colorama import Fore, Back, Style

init(convert=True) 


class CameraSettings(object):

    def __init__(self, login, timo, resolutionextra, bitextra, encodeextra, extraFPS, resolution, bitrate, encodemain,mainFPS):
        self.ip_rang = self.ip_chek()  # list of IPs
        self.login = login 
        self.resolutionextra = resolutionextra  #resolutionextra for additional
        self.bitextra = bitextra  # bitrate for additional
        self.s1 = requests.Session()  # http session
        self.timo = timo  # time-out
        self.resolution = resolution  # main resolution
        self.bitrate = bitrate  # main bitrate
        self.encodeextra = encodeextra  # Baseline =H.264B, Extended = H264. High=H264.H, Main for H264
        self.encodemain = encodemain  # Baseline =H.264B, Extended = H264 High=H264.H, Main for H264
        self.mainFPS = mainFPS
        self.extraFPS = extraFPS
        self.password = input('Enter pass for admin:')
        self.newadminpass = input('Enter new pass for admin(enter to skip)')
        if self.newadminpass == '':
            self.newadminpass = self.password
        self.new_user = input("Enter username for new user(enter to skip):")
        if self.new_user != '':
            self.newuserpass = input("Pass for new user")
        else:
            self.newuserpass = ''
        self.err_list = [] 
        self.interface = "eth0"  # network interface for dhcp
        self.smart_encode = 'true'
        # self.encodeextra = 'Main'  # Baseline =H.264B, Extended = H264. High=H264.H, Main для H264
        # self.encodemain = 'High'  # Baseline =H.264B, Extended = H264 High=H264.H, Main для H264

    def reschek(self, ip):
        if (self.bitrate < 384) or (self.bitrate > 8192):
            self.err_list.append((str(ip) + ' Invalid bitrate, changed to closest val'))
            return
        # next range is: 364-10240
        else:
            if self.bitrate > 7168 and self.resolution == "1280x720":
                self.err_list.append((str(ip) + ' Invalid bitrate, changed to closest val(7168)'))
                return
            elif self.bitrate < 1280:
                if (self.resolution == '1280x960' or self.resolution == '1280x1024') and self.bitrate < 512:
                    self.err_list.append((str(ip) + ' Invalid bitrate, changed to closest val(512)'))
                    return
                if (self.resolution == '1920x1080') and self.bitrate < 896:
                    self.err_list.append((str(ip) + ' Invalid bitrate, changed to closest val(896)'))
                    return
                if (self.resolution == '2304x1296') or (self.resolution == '2048x1536'):
                    self.err_list.append((str(ip) + ' Invalid bitrate, changed to closest val(1280)'))
                    return
        if self.bitextra < 20 or self.bitextra > 1536:
            self.err_list.append(
                (str(ip) + ' Invalid bitrate for additional stream, changed to closest val'))
        elif self.resolutionextra == '352x288' and self.bitextra > 384:
            self.err_list.append(
                (str(ip) + ' Invalid bitrate for additional stream, changed to closest val(384)'))
        elif self.resolutionextra == '704x576' and self.bitextra < 80:
            self.err_list.append(
                (str(ip) + ' Invalid bitrate for additional stream, changed to closest val(80)'))
        elif self.resolutionextra == '640x480' and self.bitextra > 384:
            self.err_list.append(
                (str(ip) + ' Invalid bitrate for additional stream, changed to closest val(1024)'))

    def check_ses(self, ip):
        try:
            self.s1.auth = HTTPDigestAuth(self.login, self.password)
            # session.auth = HTTPDigestAuth(login, password)
            r1 = self.s1.get('http://{ip}/cgi-bin/encode.cgi?action=getConfigCaps'.format(ip=ip), timeout=self.timo)

            # first letter is always Е if this is err =)
            if r1.status_code == 200:
                exp = r1.text
                if exp[0] == "E":
                    self.err_list.append(str(ip) + ' Cant connect')
                    return False
            elif (r1.status_code != 200):
                self.s1.auth = HTTPBasicAuth(self.login, self.password)
                r1 = self.s1.get('http://{ip}/cgi-bin/encode.cgi?action=getConfigCaps'.format(ip=ip), timeout=self.timo)
                if r1.status_code == 200:
                    exp = r1.text
                    if exp[0] == "E":
                        self.err_list.append(str(ip) + ' Cant connect')
                        return False
                elif r1.status_code != 200:
                    self.err_list.append(str(ip) + ' Cant connect')
                    return False

        except requests.exceptions.RequestException:
            self.err_list.append(str(ip) + ' Cant connect')
            return False

    
    def user_new(self, ip):
        """add user with check"""
        r1 = self.s1.post(
            'http://{ip}/cgi-bin/userManager.cgi?action=addUser&user.Reserved=false&user.Sharable=true&user.Name={new_user}&user.Password={newuserpass}&user.Group=user'
                .format(ip=ip,
                        new_user=self.new_user,
                        newuserpass=self.newuserpass
                        ))

        exp = str(r1.text)
        if exp[0] == 'E':
            self.err_list.append(str(ip) + ' Can not add user')
        else:
            print(ip, ' Success')

    def rebootfunk(self, ip):
        newpass = self.newadminpass
        self.s1 = requests.Session()
        self.s1.auth = HTTPDigestAuth(self.login, newpass)
        r = self.s1.get('http://{ip}/cgi-bin/magicBox.cgi?action=reboot'.format(ip=ip))
        exp = r.text
        if r.status_code == 200 and exp[0] == "E":
            self.err_list.append(str(ip) + ' Couldnt connect after reboot')
            return False

        elif r.status_code != 200:
            self.s1.auth = HTTPBasicAuth(self.login, self.newpass)
            r = self.s1.get('http://{ip}/cgi-bin/magicBox.cgi?action=reboot'.format(ip=ip))
            exp = r.text
            if r.status_code == 200 and exp[0] == "E":
                self.err_list.append(str(ip) + ' Cant connect')
                return False
        else:
            print(ip, 'Restarted - OK')

    # rebootfunk()

    # 20 fps + pass format \ bitrate
    def video_parm(self, ip):
        r1 = self.s1.post(
            'http://{ip}/cgi-bin/configManager.cgi?action=setConfig&Encode[0].MainFormat[0].Video.BitRate={'
            'bitrate}&Encode[0].MainFormat[0].Video.BitRateControl=CBR&Encode[0].MainFormat['
            '0].Video.Compression=H.264&Encode[0].MainFormat[0].Video.FPS={mainFPS}&Encode[0].MainFormat[0].Video.resolution={'
            'resolution}&Encode[0].MainFormat[0].Video.Profile={encodemain}&Encode[0].MainFormat[0].VideoEnable=true'.format(
                ip=ip,
                resolution=self.resolution,
                bitrate=self.bitrate,
                encodemain=self.encodemain,
                mainFPS=self.mainFPS))
        exp = r1.text
       
        if exp[0] == "E":
            self.videoparamsextra(ip)
            self.err_list.append((str(ip) + ' Couldnt change main resolution'))
        else:
            print(ip, ' settings for main stream changed with status', '-',
                  'OK') if r1.status_code == 200 else self.err_list.append((str(ip) + ' Main stream not configured'))

        r2 = self.s1.post(
            'http://{ip}/cgi-bin/configManager.cgi?action=setConfig&Encode[0].ExtraFormat[0].Video.resolution={'
            'resolutionextra}&Encode[0].ExtraFormat[0].VideoEnable=true&Encode[0].ExtraFormat['
            '0].Video.BitRateControl=CBR&Encode[0].ExtraFormat[0].Video.BitRate={bitextra}&Encode[0].ExtraFormat['
            '0].Video.Compression=H.264&Encode[0].ExtraFormat[0].Video.FPS={extraFPS}&Encode[0].ExtraFormat[0].Video.GOP={gopextra}&Encode[0].ExtraFormat[0].Video.Profile={encodeextra}'.format(
                ip=ip,
                bitextra=self.bitextra,
                resolutionextra=self.resolutionextra,
                encodeextra=self.encodeextra,
                extraFPS=self.extraFPS,
                gopextra=self.extraFPS*2))
        exp = r2.text

        if exp[0] == "E":
            self.err_list.append((str(ip) + ' couldnt change resol'))
        else:
            print(ip, ' configure additional stream', '-', 'OK') if r2.status_code == 200 else self.err_list.append(
                (str(ip) + ' additional stream not configured'))

    # video_parm()

    def enableDHCP(self, ip):
        r1 = self.s1.post(
            'http://{ip}/cgi-bin/configManager.cgi?action=setConfig&Network.{interface}.DhcpEnable=true'.format(
                interface=self.interface,
                ip=ip))
        exp = r1.text
        if exp[0] == "E":
            self.err_list.append(str(ip) + ' not configured DHCP')
            return False
        else:
            print(ip, 'Налаштування DHCP', '-',
                  'OK' if r1.status_code == 200 else self.err_list.append((str(ip) + 'err with DHCP')))

    
    def admin_start(self, ip):
        """change default pass"""
        if self.newadminpass == self.password:
            print(ip, 'Зміна даних для входу ', '-', 'OK')
            return

        else:
            r1 = self.s1.post(
                'http://{ip}/cgi-bin/userManager.cgi?action=modifyPassword&name={login}&pwd={newadminpass}&pwdOld={password}'.format(
                    newadminpass=self.newadminpass,
                    ip=ip,
                    password=self.password,
                    login=self.login))
            exp = r1.text
            if exp[0] == "E":
                self.err_list.append(str(ip) + 'Дані для входу не змінено')
                return False
        if r1.status_code == 200 and self.password != self.newadminpass:
            print(ip, 'Зміна даних для входу ', '-', 'OK')
        else:
            self.err_list.append((str(ip) + ' Дані для входу не змінено'))

    # admin_start()
    # password=newadminpass
    # пояс +3 і синхронізація
    def timeZone(self, ip):
        from datetime import date
        r1 = self.s1.post(
            'http://{ip}/cgi-bin/configManager.cgi?action=setConfig&NTP.TimeZone=3&NTP.Address=clock.isc.org&NTP.Port=123&NTP.Enable=true'.format(
                ip=ip))
        exp = r1.text
        if exp[0] == "E":
            self.err_list.append(str(ip) + ' NTP не налаштовано')
            return False
        else:
            print(ip, 'Налаштування NTP ', '-', 'OK') if r1.status_code == 200 else self.err_list.append(
                str(ip) + 'NTP не налаштовано')
        today = date.today()
        date = "{year}-{month}-{day} ".format(year=today.year, month=today.month, day=today.day) + strftime("%H:%M:%S",
                                                                                                            gmtime())
        r1 = self.s1.post('http://{ip}/cgi-bin/global.cgi?action=setCurrentTime&time={date}'
                          .format(ip=ip, date=date))
        exp = r1.text
        if exp[0] == "E":
            self.err_list.append(str(ip) + ' Не вдалося налаштувати час')
            return False
        else:
            print(ip, 'Налаштування часу ', '-', 'OK') if r1.status_code == 200 else self.err_list.append(
                (str(ip) + 'Час не налаштовано'))

    # смарт кодек+ всякі накладання
    def video_Smart(self, ip):
        # Відключення накладання віджетів на відео
        result = self.s1.post('http://{ip}/cgi-bin/configManager.cgi?action=setConfig' \
                              '&VideoWidget[0].TimeTitle.EncodeBlend=false' \
                              '&VideoWidget[0].Covers[0].EncodeBlend=false' \
                              '&VideoWidget[0].ChannelTitle.EncodeBlend=false' \
                              '&VideoWidget[0].CustomTitle[1].EncodeBlend=false' \
                              .format(ip=ip))
        exp = result.text
        if exp[0] == "E":
            self.err_list.append(str(ip) + ' Не вдалося налаштувати накладання')
            return False
        else:
            print(ip, 'Налаштування накладань виконано з статусом', '-',
                  'OK') if result.status_code == 200 else self.err_list.append(
                (str(ip) + 'Налаштування накладань не вдалося'))
        r2 = self.s1.get('http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=SmartEncode'.format(ip=ip))
        exp = r2.text
        # якшо помилка то перша буква буде Е =)
        if exp[0] == "E":
            r1 = self.s1.post(
                'http://{ip}/cgi-bin/configManager.cgi?action=setConfig&Encode[0].MainFormat[0].Video.GOP={gopMain}'
                    .format(
                    ip=ip,
                    gopMain=self.mainFPS*2))
            print(ip, 'SmartEncode not available', '-', 'GOP=40 OK') if r1.status_code == 200 else self.err_list.append(
                (str(ip) + 'GOP не вдалося налаштувати'))
            return 8
        else:
            result = self.s1.post(
                'http://{ip}/cgi-bin/configManager.cgi?action=setConfig&SmartEncode[0].Enable={smart_encode}'
                    .format(ip=ip,
                            smart_encode=self.smart_encode))
            print(ip, 'SmartCodec ввімкнутий з статусом', '-',
                  'OK') if result.status_code == 200 else self.err_list.append(
                (str(ip) + 'SmartCodec не ввімкнутий'))

    def videoparamsextra(self, ip):
        r1 = self.s1.post(
            'http://{ip}/cgi-bin/configManager.cgi?action=setConfig&Encode[0].MainFormat[0].Video.BitRate={'
            'bitrate}&Encode[0].MainFormat[0].Video.BitRateControl=CBR&Encode[0].MainFormat['
            '0].Video.Compression=H.264&Encode[0].MainFormat[0].Video.FPS={mainFPS}&Encode[0].MainFormat[0].Video.Profile={encodemain}&Encode[0].MainFormat[0].VideoEnable=true'.format(
                ip=ip,
                resolution=self.resolution,
                bitrate=self.bitrate,
                encodemain=self.encodemain,
                mainFPS=self.mainFPS))
        exp = r1.text
        if exp[0] == "E":
            self.err_list.append(str(ip) + ' Помилка в налаштуванні основного потоку')
            return False
        else:
            print(ip, 'Налаштування основного  потоку', '-', 'OK') if r1.status_code == 200 else self.err_list.append(
                (str(ip) + 'Помилка в налаштуванні основного потоку, спробуйте змінити бітрейт'))

        r2 = self.s1.post(
            'http://{ip}/cgi-bin/configManager.cgi?action=setConfig&Encode[0].ExtraFormat[0].VideoEnable=true&Encode[0].ExtraFormat['
            '0].Video.BitRateControl=CBR&Encode[0].ExtraFormat[0].Video.BitRate={bitextra}&Encode[0].ExtraFormat['
            '0].Video.Compression=H.264&Encode[0].ExtraFormat[0].Video.FPS={extraFPS}&Encode[0].ExtraFormat[0].Video.GOP={gopextra}&Encode[0].ExtraFormat[0].Video.Profile={encodeextra}'.format(
                ip=ip,
                bitextra=self.bitextra,
                resolutionextra=self.resolutionextra,
                encodeextra=self.encodeextra,
                extraFPS=self.extraFPS,
                gopextra=self.extraFPS * 2
            ))
        # print(r2.text, r2.status_code)
        exp = r2.text

        if exp[0] == "E":
            self.err_list.append(str(ip) + ' Не вдалося налаштувати додатковий потік')
            return False
        else:
            print(ip, 'Налаштування додаткового  потоку', '-', 'OK') if r2.status_code == 200 else self.err_list.append(
                (str(ip) + 'Помилка, спробуйте змінити бітрейт'))

    # для вибору і перевірки resolution
    def ui(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/encode.cgi?action=getConfigCaps'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'caps[0].SnapFormat[0].Video.ResolutionTypes='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('caps[0].SnapFormat[0].Video.ResolutionTypes=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break

            # print (result)

        b = {'1080P': '1920x1080', 'SXGA': '1280x1024', '720P': '1280x720', 'D1': '704x576', 'VGA': '640x480',
             'CIF': '352x288', 'QCIF': '176x144',
             'QVGA': '320x240'}
        for resol in text:
            if resol in b:
                text[text.index(resol)] = b[resol]

        resolex = ['704x576', '640x480', '352x288', '176x144', '320x240']
        textnew = []
        for res in text:
            if res in resolex:
                textnew.append(res)
        if self.resolution not in text:
            output = list(range(1, len(text) + 1))
            resold = dict(zip(text, output))
            for key, value in resold.items():
                print(value, '-', key)
            k = int(input('Виберіть роздільну здатність із списку: '))
            for key, value in resold.items():
                if resold[key] == k:
                    self.resolution = key
            print('Вибір:', self.resolution)

        if self.resolutionextra not in textnew:
            outextra = list(range(1, len(textnew) + 1))
            resold = dict(zip(textnew, outextra))
            for key, value in resold.items():
                print(value, '-', key)
            k = int(input('Виберіть роздільну здатність для додаткового потоку із списку: '))
            for key, value in resold.items():
                if resold[key] == k:
                    self.resolutionextra = key
            print('Вибір:', self.resolutionextra)

    ###---------- Далі куча геттерів -----------###
    def MainBitrate(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].MainFormat[0].Video.BitRate='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].MainFormat[0].Video.BitRate=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        return ('bit=', text)

    def MainCBR(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].MainFormat[0].Video.BitRateControl='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].MainFormat[0].Video.BitRateControl=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        return ('cbr=', text)

    def MainFPS(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].MainFormat[0].Video.FPS='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].MainFormat[0].Video.FPS=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        return ('fps=', text)

    def MainGOP(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].MainFormat[0].Video.GOP='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].MainFormat[0].Video.GOP=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        r2 = self.s1.get('http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=SmartEncode'.format(ip=ip))
        smart = r2.text
        return ('gop=', text, smart)

    def MainResolution(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].MainFormat[0].Video.resolution='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].MainFormat[0].Video.resolution=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        return (ip, 'resol=', text)

    def ExtraResolution(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].ExtraFormat[0].Video.resolution='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].ExtraFormat[0].Video.resolution=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        return (ip, 'resol=', text)

    def ExtraBitrate(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].ExtraFormat[0].Video.BitRate='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].ExtraFormat[0].Video.BitRate=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        return ('bit=', text)

    def ExtraCBR(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].ExtraFormat[0].Video.BitRateControl='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].ExtraFormat[0].Video.BitRateControl=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        return ('cbr=', text)

    def ExtraFPS(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].ExtraFormat[0].Video.FPS='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].ExtraFormat[0].Video.FPS=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        return ('fps=', text)

    def ExtraGOP(self, ip):
        r1 = self.s1.get(
            'http://{ip}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'
                .format(ip=ip))
        text = r1.text.split('\n')
        searchtitle = 'table.Encode[0].ExtraFormat[0].Video.GOP='
        for i in text:
            # result = re.search('\Acaps[0].MainFormat[0].Video.ResolutionTypes=',i)
            if searchtitle in i:
                j = text.index(i)
                i = 0
                text = text[j]
                text = text.replace('table.Encode[0].ExtraFormat[0].Video.GOP=', '')
                text = text.replace("'", '')
                text = list(text.split(','))
                text[len(text) - 1] = text[len(text) - 1].replace('\r', '')
                break
        return ('gop=', text)

    ### ------ ------ ###
    def ip_chek(self):
        ip_rang = []
        start = (input('enter start_ip: '))
        finish = (input('enter finish_ip: '))
        if finish >= start:
            try:
                for ip_int in range(int(ipaddress.IPv4Address(start)), int(ipaddress.IPv4Address(finish)) + 1):
                    ip_rang.append(str(ipaddress.IPv4Address(ip_int)))
            except:
                self.ip_chek()
        elif finish == '':
            finish = start
            ip_rang.append(str(ipaddress.IPv4Address(int(ipaddress.IPv4Address(start)))))
            return ip_rang
        else:
            print(Fore.RED + 'неправильно введені адреси ')
            print(Fore.RESET + Back.RESET + Style.RESET_ALL)
            self.ip_chek()
        return ip_rang

    def main(self):
        try:
            self.bitrate = int(input(
                "Бітрейт для основного потоку(enter щоб пропустити - стандартний 1024): "))  # бітрейт основногопотоку з клави
        except:
            print(' Поставлено стандартний бітрейт 1024')
            self.bitrate = 1024
        #####  ####--------------------------------#### ####
        f_list = ['user_new', 'timeZone', 'enableDHCP', 'video_parm', 'video_Smart',
                  'admin_start']  # cписок доступних функцій
        f_index = list(range(1, len(f_list) + 1))
        f_dict = dict(zip(f_list, f_index))
        print(f_dict)
        name = (input('Виберіть функції зі списку(enter для всіх): '))
        if name == '\n' or name == '':
            func_list = f_list
        else:
            name = [f_numn.strip() for f_numn in name.split(',')]
            func_list = []
            for key, value in f_dict.items():
                if str(f_dict[key]) in name:
                    func_list.append(key)
        # умова коли потрібен перезапуск
        if 'video_Smart' in func_list:
            func_list.append('rebootfunk')
        for ip in self.ip_rang:
            # пробігаємо ip
            # перевірка аутентифікації
            if self.check_ses(ip) is False:
                continue  # якщо False то на наступну ip
            else:
                """
                  Для отримання даних  по потоках 
                print(ip,self.ExtraResolution(ip),self.ExtraBitrate(ip),self.ExtraCBR(ip),self.ExtraFPS(ip), self.ExtraGOP(ip))
                print('mainformat',ip, self.MainResolution(ip),self.MainBitrate(ip), self.MainCBR(ip), self.MainFPS(ip), self.MainGOP(ip))
                """
                self.reschek(ip)  # перевірка відповідності бітрейту до розд здатності
                self.ui(ip)  # для вибору розд здатності, з списку доступних, якщо вказано невірно + перевірка
                for func_n in func_list:
                    func = getattr(self, func_n)
                    func(ip)

        k = input('Якщо ви хочете додати налаштування, натисніть y, якщо ні- будь-яку клавішу: ')
        if k == 'Y' or k == 'y':
            self.main()
        else:
            if self.err_list:
                print(Fore.BLUE + '\t\t Cписoк помилок')
                for errors in self.err_list:
                    print(Fore.GREEN + errors)


### ------------------------END OF CLASS ------------------------- ###


"""
self.encodeextra = 'Main'  # Baseline =H.264B, Extended = H264. High=H264.H, Main для H264
self.encodemain = 'High'  # Baseline =H.264B, Extended = H264 High=H264.H, Main для H264
login це той під яким будуть проводитись налаштування, пароль і параметри нового користувача запитуватимуться в користувача
timo=timeout
решта змінних описані в методі __init__
video_parm - основна функція по налаштуванню відео, в запитах можна змінити параметри( CBR,FPS)
videoparamsextra - якщо не виставляється resolution ( нові прошивки)
"""
inst = CameraSettings(login='test1', timo=2.5, resolutionextra='352x288', bitextra=160, encodeextra='Main', extraFPS=8,
                      resolution='1920x1080', bitrate='1024', encodemain='Main', mainFPS=20)
inst.main()  # метод, який робить всю магію
# (self,ip_rang,login,resolutionextra,bitextra,timo,resolution,bitrate,encodeextra,encodemain)
# (self,login,timo,resolutionextra,bitextra,encodeextra,resolution,bitrate,encodemain)
#     func()
"""
далі новий екземпляр
"""
# inst2 = CameraSettings(login='test1',timo=2.5,resolutionextra='352x288',bitextra=224,encodeextra='Main',extraFPS=8,
#                           resolution='1280x720',bitrate=4096,encodemain='High',mainFPS=20)
# inst2.main()
