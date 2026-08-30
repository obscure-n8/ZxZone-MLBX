def bin_name(index):
    names = ["aria2c", "qbittorrent-nox", "ffmpeg", "rclone", "sabnzbdplus"]
    if index < len(names):
        return names[index]
    return names[0]
