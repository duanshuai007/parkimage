FROM ubuntu

ENV LANG C.UTF-8
ENV TZ=Asia/Shanghai

RUN buildDeps='expect sudo rsync net-tools ssh python3 python3-tk python3-pip' \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y $buildDeps \
 && pip3 install Pillow \
 && pip3 install tornado \
 && rm -rf /root/.cache/pip/wheels/* \
 && rm -rf /usr/share/python-wheels/* \
 && apt-get purge -y --auto-remove python3-pip \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get autoremove \
 && apt-get clean

RUN echo "root:123" | chpasswd \
 && adduser duan --disabled-password \
 && echo "duan:123" | chpasswd \
 && echo "duan ALL=(ALL:ALL) ALL" >> /etc/sudoers

COPY ./backserver.tar.gz /home/duan/
WORKDIR /home/duan
RUN tar -zxvf backserver.tar.gz \
 && chown -R duan:duan /home/duan \
 && rm backserver.tar.gz \
 && find -name *.git* | xargs rm -rf 

USER duan
RUN export DISPLAY=:0
#ENTRYPOINT su - duan -c "/home/duan/backserver/install_crontask.sh 192.168.1.123"
