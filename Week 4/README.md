# Git-Heat

## Running the code

1. The package has 2 dependencies

    <pre>
    pip install pycryptodome
    pip install diffiehellman
    </pre>

2. Put the absolute path of each file to be shared in '.config' file, one file on each line.

3. Run the server on the computer which wishes to share the file.

    `
    python3 server.py
    `

4. Run the client on the computer which wishes to download the file.

    `
    python3 client.py
    `


## Tools Used

Language: Python 3.6
Dependencies: Pycryptodome, diffiehellman

## Concept

Networking, Cryptography 

## Information

1. The tool uses Diffie-Hellman key exchange protocol to exchange private keys.
2. The private keys are then used with Advanced Encryption Algorithm to exchange files.
3. Diffie-Hellman is slow and so key exchange takes time. There is currently no good alternative to this to work on distributed network.
4. The tool is tested to support download of files upto 3 GB. The download depends on the reliability of underlying TCP layer. Unlike existing file sharing tools, I have not implemented reliability at application layer. The files are hashed so that user will receive information whether a download succeded or not.
5. At application layer the tool makes use of Loadra File Transfer Protocol (LFTP).

## Loadra File Transfer Protocol (LFTP)

### General Format

<pre>
HEADER
BODY
</pre>

### Key Exchange (2479 Bytes)

<pre>
KEY_EXCHANGE
&lt;Public Key of Sender&gt;
</pre>

### File List Header (29 Bytes)

<pre>
FILELIST
&lt;Number of segments (each of 1024 bytes) required for file list&gt;
</pre>

### File List Body

<pre>
1024 bytes of content
</pre>

### Ready Signal (5 Bytes)

<pre>
READY
</pre>

### Acknowledgement (3 Bytes)

<pre>
ACK
</pre>

### Requesting a file (28 Bytes)

<pre>
REQUEST
&lt;Fully Qualified File Name&gt;
</pre>

### File Transfer Header (25 Bytes)

<pre>
FILE
&lt;Name of the File&gt;
&lt;Number of segments (each of 1024 bytes) required for file&gt;
</pre>

### File Transfer Body

<pre>
1024 bytes of content
</pre>