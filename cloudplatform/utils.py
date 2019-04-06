def htoi(host):
    part = host.split('.')
    result = 0
    for tmp in part:
        result = (result << 8) + int(tmp)
    return result


def itoh(int_host):
    part = [str((int_host & 0xff000000) >> 24),
            str((int_host & 0x00ff0000) >> 16),
            str((int_host & 0x0000ff00) >> 8),
            str((int_host & 0x000000ff) >> 0)]
    result = part[0] + '.' + part[1] + '.' + part[2] + '.' + part[3]
    return result


if __name__ == "__main__":
    ip = '127.0.0.1'
    digit = htoi(ip)
    after_ip = itoh(digit)
    print("ip to digit:" + str(digit))
    print("digit to ip:" + after_ip)
