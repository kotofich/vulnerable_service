#include <unistd.h>
#include <stdlib.h>

/* Добавляем комментарий, который точно попадет в strings */
char *info = "Executing command: id"; 

int main() {
    setuid(0);
    setgid(0);
    // Вызываем id. Пробел в конце поможет strings (3 символа)
    system("id "); 
    return 0;
}