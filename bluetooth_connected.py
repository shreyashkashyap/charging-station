import sys, asyncio, re
from asyncio.subprocess import PIPE

re_conn = re.compile('.*Device ([0-9A-Z:]+) Connected: (yes|no).*')

init_strings = [
    b'power on\r',
    b'discoverable on\r',
    b'pairable on\r',
    b'agent NoInputNoOutput\r',
    b'default-agent\r'
]

class BT:
    def __init__(self):
        self.p = None
        self.ready = False
        self.init_step = -1
        self.init_done = False
        self.no_data_cnt = 0
        self.conn_dev = None
        self.new_dev = None


    async def send(self, s):
        print('  >> {}'.format(s))
        self.p.stdin.write(s)
        await self.p.stdin.drain()

    async def read(self):
        try:
            l = await asyncio.wait_for(self.p.stdout.readline(), 1)
        except asyncio.TimeoutError:
            pass
        else:
            if l is None:
                raise Exception('EOF')
            print('  << {}'.format(l))
            return l
        return None

    async def handle(self, l):
        if l is None:
            if self.init_step == -1:
                self.ready = True
                self.init_step = 0
            elif self.init_step < len(init_strings) and self.no_data_cnt > 2:
                self.ready = True
            else:
                return

        if l is not None and ('succeeded' in l or 'Agent registered' in l or 'Default agent request successful' in l):
            self.init_step += 1
            self.ready = True

        if self.ready and self.init_step < len(init_strings):
            await self.send(init_strings[self.init_step])
            self.ready = False
            return
        elif self.ready:
            if not self.init_done:
                self.init_done = True
                await self.send(b'disconnect\r')

        match = re_conn.match(l)
        if match:
            dev = match.group(1)
            connected = match.group(2)
            if connected == 'yes':
                if self.conn_dev is not None and dev != self.conn_dev:
                    await self.send(b'disconnect\r')
                    self.new_dev = dev
                else:
                    print('New device connected: {}'.format(dev))
                    self.conn_dev = dev
                return
            else:
                if self.conn_dev is not None and dev == self.conn_dev:
                    print('Device disconnected: {}'.format(dev))
                    self.conn_dev = None

        if 'Successful disconnected' in l:
            if self.new_dev is not None:
                await self.send(bytes('connect {}\r'.format(self.new_dev), 'utf-8'))
            return

        if 'Connection successful' in l:
            print('New device connected: {}'.format(self.new_dev))
            self.conn_dev = self.new_dev
            self.new_dev = None
            return

        if 'KAuthorize service' in l:
            await self.send(b'yes\r')
            return

        if 'Failed to connect: org.bluez.Error.Failed' in l:
            if self.new_dev is not None:
                await self.send(bytes('connect {}\r'.format(self.new_dev), 'utf-8'))
            return


    async def run(self):
        self.p = await asyncio.create_subprocess_shell('bluetoothctl', stdin=PIPE, stdout=PIPE)

        while True:
            try:
                l = await self.read()
            except:
                break
            else:
                if l is None:
                    self.no_data_cnt += 1
                    await self.handle(None)
                else:
                    self.no_data_cnt = 0
                    await self.handle(str(l))
                continue

        return await self.p.wait()

bt = BT()
loop = asyncio.get_event_loop()
loop.run_until_complete(bt.run())