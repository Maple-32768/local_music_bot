import asyncio
import discord
from discord.ext import commands
from datetime import datetime

zpl_file_prefix = '<media src=\"'
zpl_file_suffix = '\" albumTitle=\"'
bot_command_prefix = '//'
client = commands.Bot(command_prefix=bot_command_prefix)
ffmpeg_exe = r'./ffmpeg/ffmpeg.exe'
ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 0'}


def load(path: str):
    if not path.endswith('.zpl'):
        return

    music_path = []
    with open(path, mode='r', encoding='UTF-8') as f:
        for line in f:
            if zpl_file_prefix in line:
                path1 = line[line.find(zpl_file_prefix) + len(zpl_file_prefix):]
                path1 = path1[0:path1.find(zpl_file_suffix)]
                music_path.append(path1)
    return music_path


zpl_path = r'C:\Users\owner\Music\Playlists\原神OST.zpl'
musics = []
vc = None
pausing = False
loop_mode = 0


@client.event
async def on_ready():
    print('[' + str(datetime.now()) + '] Launch successful')


@client.command()
async def connect(ctx):
    if not ctx.message.guild:
        return False

    if ctx.author.voice is None:
        await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                           description='ボイスチャンネルに接続していません\nボイスチャンネルに接続してから再度実行してください'))
        return False
    elif ctx.guild.voice_client:
        if ctx.author.voice.channel == ctx.guild.voice_client.channel:
            await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                               description='既に接続済みです'))
            return False
        else:
            voice_channel = ctx.author.voice.channel
            await ctx.voice_client.move_to(voice_channel)
            return True
    else:
        await ctx.send(embed=discord.Embed(title='ボイスチャンネル接続', color=0x00ff00,
                                           description='**' + ctx.guild.name + ' : ' + ctx.author.voice.channel.name
                                                       + '**に接続しました'))
        await ctx.author.voice.channel.connect()
        global vc
        vc = ctx.guild.voice_client
        print(
            '[' + str(datetime.now()) + '] Connected [' + ctx.guild.name + ' : ' + ctx.author.voice.channel.name + ']')
        return True


@client.command()
async def join(ctx):
    return await connect(ctx)


@client.command()
async def disconnect(ctx):
    if not ctx.message.guild:
        return

    if ctx.voice_client is None:
        await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                           description='まだボイスチャンネルに接続していません'))
    else:
        await ctx.voice_client.disconnect()
        await ctx.send(embed=discord.Embed(title='ボイスチャンネル切断', color=0x00ff00,
                                           description='切断しました'))
        print('[' + str(
            datetime.now()) + '] Disconnected [' + ctx.guild.name + ' - ' + ctx.author.voice.channel.name + ']')


@client.command()
async def leave(ctx):
    await disconnect(ctx)


@client.command()
async def p(ctx):
    await play(ctx)


@client.command()
async def play(ctx):
    global musics
    if len(musics) == 0:
        musics = load(zpl_path)

    if ctx.guild.voice_client is None:
        joined = await join(ctx)
        if not joined:
            return

    if not ctx.guild.voice_client.is_playing():
        await play1()


async def play1():
    while len(musics) > 0:
        if vc is None:
            break
        vc.play(discord.FFmpegPCMAudio(musics[0], executable=ffmpeg_exe))
        while vc.is_playing() or pausing:
            await asyncio.sleep(5)
        if len(musics) != 0 and loop_mode != 2:
            if loop_mode == 1:
                musics.append(musics[0])
            musics.pop(0)


@client.command()
async def remove(ctx, *args):
    if len(args) != 1 or not args[0].isdicimal():
        await ctx.send(embed=discord.Embed(title='使用方法', color=0xffff00,
                                           description='//remove [キュー番号]'))
        return

    if len(musics) < int(args[0]) or int(args[0]) != float(args[0]) or int(args[0]) <= 0:
        await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                           description='キュー番号が無効です'))
        return

    musics.pop(args[0])


@client.command()
async def skip(ctx):
    if vc is None:
        await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                           description='現在再生中ではありません'))
        return
    vc.pause()


@client.command()
async def pause(ctx):
    global pausing
    if vc is None or pausing:
        await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                           description='現在再生中ではありません'))
        return
    else:
        pausing = True
        vc.pause()
        await ctx.send(embed=discord.Embed(title='一時停止', color=0xffff00,
                                           description='現在一時停止中です。\n`//resume`で再生を再開出来ます。'))


@client.command()
async def resume(ctx):
    global pausing
    if vc is None:
        await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                           description='現在再生中ではありません'))
        return
    elif not pausing:
        await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                           description='現在一時停止中ではありません'))
        return
    else:
        pausing = False
        vc.resume()
        await ctx.send(embed=discord.Embed(title='再生中', color=0x00ff00,
                                           description='再生を再開しました'))


@client.command()
async def stop(ctx):
    global musics
    if vc is None:
        await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                           description='現在再生中ではありません'))
        return
    musics = []
    vc.pause()


@client.command()
async def loop(ctx):
    if ctx.guild.voice_client is None:
        await ctx.send(embed=discord.Embed(title='エラー', color=0xffff00,
                                           description='まだボイスチャンネルに接続していません'))
        return
    global loop_mode
    loop_mode = (loop_mode + 1) % 3
    lp = loop_mode
    if lp == 1:
        await ctx.send(embed=discord.Embed(title='ループ', color=0x00ff00,
                                           description='プレイリストをループします'))
    elif lp == 2:
        await ctx.send(embed=discord.Embed(title='ループ', color=0x00ff00,
                                           description='現在の曲をループします'))
    else:
        await ctx.send(embed=discord.Embed(title='ループ', color=0x00ff00,
                                           description='ループが無効になりました'))


@client.event
async def on_message(message):
    if message.content.startswith(bot_command_prefix):
        command = message.content.replace(bot_command_prefix, '')
        if '\u0020' in command:
            command = command[0:message.content.find('\u0020') - 2]
        if command in [com.name for com in client.commands]:
            await client.process_commands(message)
        else:
            await message.channel.send('Unknown command')


client.run('ODc0NTM3NjE3NDY1Njk2MjY2.YRIaoA.sG3L1H8YXC9E5B-qyMbgtp-gJt8')
